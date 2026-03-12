# Security Architecture — CosmoTarot

**Version:** 1.0
**Date:** March 2026
**Author:** Gibran (gibranol)

---

## Threat Model

CosmoTarot is a mobile-first AI application where users share personal data (birth date, life questions) and pay for premium features. The primary threats are:

| Threat | Impact | Likelihood |
|--------|--------|-----------|
| Prompt injection via user question | AI persona hijacking, system prompt leak | High |
| JWT theft / replay | Unauthorized access to another user's readings | Medium |
| Brute-force login | Account takeover | Medium |
| XSS via stored readings | Malicious script execution in web context | Low-Medium |
| SQL injection via input fields | Data exfiltration, DB corruption | Low (parameterized queries) |
| API billing abuse (Gemini DoS) | Inflated AI costs | Medium |
| Supabase key leak | Full DB access, auth bypass | Low (env var management) |

---

## Defense in Depth

Security is applied at every layer. No single layer is trusted alone.

```
┌─────────────────────────────────────────────────────┐
│  Flutter App  (untrusted — no secrets stored here)  │
│  └── JWT in flutter_secure_storage                  │
│  └── Certificate pinning (MITM prevention)          │
│  └── Code obfuscation (release builds)              │
├─────────────────────────────────────────────────────┤
│  FastAPI Backend  (trusted boundary)                │
│  └── Rate limiting (slowapi) on all endpoints       │
│  └── Input sanitization on every user string        │
│  └── JWT validation via Supabase                    │
│  └── Premium gate enforcement (server-side)         │
│  └── CORS restricted to app domain (production)     │
├─────────────────────────────────────────────────────┤
│  PostgreSQL (Supabase)                              │
│  └── Row Level Security (RLS) on all tables         │
│  └── Parameterized queries (SQLModel/SQLAlchemy)    │
│  └── SSL/TLS enforced                               │
├─────────────────────────────────────────────────────┤
│  Third-Party APIs                                   │
│  └── Gemini: key server-side only, no PII sent      │
│  └── RevenueCat: webhook signature verification     │
│  └── Supabase: service_role key never in Flutter    │
└─────────────────────────────────────────────────────┘
```

---

## Layer 1: Frontend Security (Flutter)

**Rule: The Flutter app is untrusted. It never stores or handles secrets.**

- No API keys in Flutter code (no Gemini key, no Supabase `service_role` key)
- No direct database access from Flutter
- All AI calls route through FastAPI: `Flutter → FastAPI → Gemini`
- JWT stored in `flutter_secure_storage` (iOS Keychain / Android EncryptedSharedPreferences)
- Certificate pinning for API calls (prevents MITM attacks)
- `--obfuscate --split-debug-info` for release builds
- Deep link validation (prevent malicious redirect attacks)

---

## Layer 2: API Gateway (FastAPI)

### Rate Limiting (slowapi)

| Endpoint | Limit | Reason |
|----------|-------|--------|
| `POST /api/auth/login` | 5 req / 15 min per IP | Brute-force prevention |
| `POST /api/auth/register` | 3 req / hour per IP | Spam account prevention |
| `POST /api/tarot/ask` | 10 req / hour per user | AI cost control |
| `POST /api/compatibility/check` | 5 req / hour per user | AI cost control |
| `GET /api/tarot/daily` | 30 req / hour per user | Abuse prevention |
| Global | 100 req / min per IP | DDoS basic protection |

### CORS

- Development: `*` (any origin)
- Production: only the Flutter app's domain
- `allow_credentials: true`
- No wildcard in production

### Request Validation

- Pydantic V2 validates all request bodies automatically
- `model_config: extra = "forbid"` — unexpected fields are rejected
- Max request body size: 1MB
- Type coercion disabled (strict types)

---

## Layer 3: Input Sanitization

**All user text inputs pass through `sanitize_input()` BEFORE processing or AI submission.**

Source: `app/security/sanitizer.py`

### Steps applied (in order)

```
1. Strip null bytes and ASCII control characters (prevents log injection)
2. Enforce max length BEFORE escaping (prevents byte-count bypass tricks)
3. Remove dangerous HTML tags: <script>, <iframe>, <object>, <embed>, <form>...
4. Escape remaining HTML entities (< → &lt;, > → &gt;, & → &amp;, " → &quot;)
5. Block prompt injection patterns:
   - "ignore (previous|all) instructions"
   - "act as [persona]"
   - "system prompt"
   - "you are now"
   - "forget everything"
   - "new instructions:"
```

### What we protect against

| Attack | Defense |
|--------|---------|
| XSS | HTML entity escaping + dangerous tag removal |
| Stored XSS | Output is never rendered as raw HTML |
| Prompt injection | Regex pattern detection → 400 error |
| AI cost inflation | Max 500 chars per question |
| Log injection | Null byte and control char stripping |

---

## Layer 4: Authentication & Authorization

### JWT Flow

```
1. User authenticates with Supabase (email/Google/Apple)
2. Supabase returns access_token (JWT) + refresh_token
3. Flutter stores both in flutter_secure_storage
4. Every API request: Flutter sends JWT in Authorization: Bearer <token>
5. FastAPI calls supabase.auth.get_user(token) to validate
6. If valid: loads User from our DB, returns user object
7. If invalid/expired: raises 401 Unauthorized
```

### What we validate on every request

- JWT signature (Supabase verifies cryptographic signature)
- JWT expiration (`exp` claim)
- User exists in our `users` table (defense against orphaned Supabase accounts)
- For premium endpoints: `user.is_premium == True` (enforced server-side, not UI)

### IDOR Prevention

- Users can only access their own readings (`WHERE user_id = current_user.id`)
- No endpoint exposes another user's data
- Reading IDs are UUIDs (not sequential integers that could be enumerated)

---

## Layer 5: Data Protection

### Secrets Management

| Secret | Location | Never in |
|--------|----------|---------|
| `SUPABASE_SERVICE_ROLE_KEY` | `.env` on backend | Flutter, git |
| `GEMINI_API_KEY` | `.env` on backend | Flutter, git |
| `REVENUECAT_WEBHOOK_SECRET` | `.env` on backend | Flutter, git |
| `SUPABASE_ANON_KEY` | `.env` on backend | git (publicly guessable but not committed) |

`.env` is in `.gitignore`. `.env.example` with placeholder values is committed.

### Database Security

- Row Level Security (RLS) enabled on all Supabase tables
- Users can only read/write their own rows via RLS policies
- `service_role` key used only for admin operations
- Connection via Session Pooler (port 5432, IPv4) with SSL/TLS
- Parameterized queries via SQLModel/SQLAlchemy Core (no raw SQL with user input)

### Data Privacy

- Minimal data collection: only what is needed for the features
- Birth time and birth city are **optional**
- No third-party analytics SDKs in MVP
- GDPR-ready: users can delete their account and all associated data
- No PII sent to Gemini: only zodiac sign, card names, anonymized question

---

## Layer 6: Third-Party API Security

### Gemini

- API key stored server-side only
- User input sanitized **before** sending to Gemini
- No user PII in prompts (only zodiac sign, cards, cleaned question)
- Response validated before returning to user
- Timeout: 30 seconds max
- Fallback responses for all failure modes (see `services/ai.py`)

### RevenueCat Webhooks

```
POST /webhooks/revenuecat

Security:
  1. Read X-RevenueCat-Signature header
  2. HMAC-SHA256 verify against REVENUECAT_WEBHOOK_SECRET
  3. Reject with 401 if signature is invalid
  4. Process idempotently (handle duplicate events safely)
  5. Respond 200 immediately, process in background
```

---

## Automated Security Tests

Run with: `bandit -r app/ -ll`

| Test suite | What it covers |
|------------|---------------|
| `tests/unit/test_sanitizer.py` | Unit tests for sanitize_input() |
| `tests/integration/test_security_integration.py` | XSS, prompt injection, JWT tampering, SQL injection, rate limits |
| `bandit` (CI) | Static analysis: hardcoded passwords, subprocess injection, etc. |
| `safety` (CI) | Known CVEs in Python dependencies |

---

## Incident Response

### If a secret is leaked (git history or log)

1. **Immediately rotate** the compromised key (Supabase dashboard / Google Cloud Console)
2. Check git history: `git log --all -S "leaked_value"`
3. Remove from history with BFG Repo Cleaner or `git filter-repo`
4. Force-push cleaned history (coordinate with team)
5. Audit Supabase logs for unauthorized access during the exposure window
6. Document in `BUG_LEDGER.md`

### If a user reports account compromise

1. Invalidate all sessions: Supabase dashboard → Users → Sign out all sessions
2. Reset password
3. Check `daily_readings` and `tarotist_questions` for unauthorized reads
4. Notify user with timeline of access

### If rate limits are being abused

1. Temporarily lower limits in `app/api/*.py` (deploy hotfix)
2. Add IP to Supabase's Edge Function blocklist if available
3. Consider CAPTCHA on login for repeated violations

---

## Dependency Update Policy

- Run `safety check` in CI on every push
- Review `pip-audit` output monthly
- Update dependencies with known CVEs within 7 days of disclosure
- Pin major versions in `requirements.txt`; allow minor/patch updates

---

## OWASP Top 10 Coverage

| OWASP Category | Control |
|----------------|---------|
| A01 Broken Access Control | JWT validation, IDOR prevention, premium gates |
| A02 Cryptographic Failures | No secrets in code, HTTPS enforced, Supabase bcrypt |
| A03 Injection | Parameterized queries, input sanitization, Pydantic validation |
| A04 Insecure Design | Threat model documented, defense in depth |
| A05 Security Misconfiguration | CORS restricted in production, RLS enabled |
| A06 Vulnerable Components | `safety` scan in CI |
| A07 Auth & Session Failures | Supabase JWT, refresh token rotation, rate limiting |
| A08 Software Integrity | Signed commits, webhook signature verification |
| A09 Logging & Monitoring | Logging on auth failures, blocked injections |
| A10 SSRF | No user-controlled URL fetching in backend |

---

*This document is maintained as a living portfolio piece. Update after each security-relevant change.*
