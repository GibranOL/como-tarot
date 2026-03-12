# 🔮 CosmoTarot — Development Roadmap v2.0

**Version:** 2.0
**Date:** March 2026
**Author:** Gibran (gibranol)
**Builder:** Claude Code (terminal)
**QA Reviewer:** Claude (chat)

---

## 📋 Project Summary

CosmoTarot is a mobile-first tarot, numerology, and astrology app powered by AI. Users receive personalized tarot readings, daily horoscopes, numerology insights, and birth charts — all enhanced by AI-generated interpretations that adapt to each user's profile and preferences.

**Future vision:** Asian expansion (Saju, Chinese Lunar Calendar, I Ching).

---

## 🏗️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | Flutter (Dart) | One codebase for iOS + Android + web later. Superior animation capabilities for mystical UI |
| **Backend** | FastAPI (Python) | Modern, fast, auto-docs (Swagger), async support, great for AI integration |
| **Database** | Supabase (PostgreSQL) | Real PostgreSQL, built-in auth, generous free tier, no vendor lock-in |
| **AI Engine** | Google Gemini 2.0 Flash | Cheapest option for creative content, multilingual, generous free tier |
| **Auth** | Supabase Auth (Google + Apple + Email) | Zero API cost, Apple Sign-In required for iOS, all three built into Supabase |
| **Payments** | RevenueCat | Cross-platform subscription management for iOS + Android |
| **CI/CD** | GitHub Actions | Free for public repos, great for QA portfolio |
| **Testing** | pytest + pytest-cov | Industry standard for Python, coverage reporting |
| **Linting** | ruff | Ultra-fast Python linter |
| **Security** | bandit + safety | Vulnerability scanning |
| **Animations** | Lottie + Flutter particles | Pre-made animations + custom cosmic effects |
| **Card Art** | Google ImageFX (AI-generated) | 78 unique tarot cards, consistent mystical style |

---

## 💰 Monetization: Freemium Model

**Pricing (numerology-themed):**
- Monthly: **$4.44/month**
- Annual: **$44.44/year** (saves ~17%)

| Feature | Free | Premium ($4.44/mo) |
|---------|------|---------------------|
| Daily 3-card tarot reading | 1/day | Unlimited |
| AI tarot interpretation | Basic | Deep & personalized |
| Daily horoscope | ✅ | ✅ |
| Numerology (life number) | ✅ | ✅ |
| Zodiac compatibility | ❌ | ✅ |
| Birth chart / natal chart | ❌ | ✅ |
| Ask the Tarotist (AI Q&A) | 1/day | Unlimited |
| Reading history | Last 7 days | Unlimited |

---

## 🌐 Languages

- **MVP:** Spanish + English (i18n built into architecture from day one)
- **Future:** Portuguese, French (large tarot markets)

---

## 🛡️ Security Architecture (Portfolio Highlight)

This section documents the security strategy for CosmoTarot. It's designed to be a standalone portfolio piece demonstrating security awareness in a real-world application.

### Principle: Defense in Depth

Security is applied at every layer — frontend, API, backend, database, and third-party integrations. No single layer is trusted alone.

### Layer 1: Frontend Security (Flutter)

```
Rule: The Flutter app is UNTRUSTED. It never stores or handles secrets.

├── NO API keys in Flutter code (no Gemini key, no Supabase service_role key)
├── NO direct database access from Flutter
├── All AI calls go through FastAPI backend (Flutter → FastAPI → Gemini)
├── JWT stored in flutter_secure_storage (encrypted keychain on iOS, encrypted prefs on Android)
├── Certificate pinning for API calls (prevents MITM attacks)
├── Obfuscate Dart code for release builds (--obfuscate --split-debug-info)
└── Deep link validation (prevent malicious redirects)
```

### Layer 2: API Gateway Security (FastAPI)

```
Rate Limiting (slowapi):
├── POST /api/auth/login       → 5 requests / 15 min per IP
├── POST /api/auth/register    → 3 requests / hour per IP
├── POST /api/tarot/ask        → 10 requests / hour per user
├── POST /api/compatibility    → 5 requests / hour per user
├── GET  /api/tarot/daily      → 30 requests / hour per user
└── Global                     → 100 requests / min per IP

CORS Configuration:
├── Allow only specific origins (your Flutter app domain)
├── No wildcard (*) in production
└── Credentials: true (for JWT cookies if needed)

Request Validation:
├── Pydantic V2 validates ALL request bodies automatically
├── Max request body size: 1MB
├── Reject unexpected fields (model_config: extra = "forbid")
└── Type coercion disabled (strict mode)
```

### Layer 3: Input Sanitization

```
All user text inputs pass through sanitizer BEFORE processing:

sanitize_input(text) → cleaned_text
├── XSS Prevention
│   ├── Escape HTML entities (< > & " ')
│   ├── Strip <script>, <iframe>, <object> tags
│   └── Encode output when rendering
├── Prompt Injection Prevention
│   ├── Detect patterns: "ignore instructions", "act as", "system prompt"
│   ├── Block requests containing injection attempts (return 400)
│   └── Log blocked attempts for monitoring
├── SQL Injection Prevention
│   ├── SQLModel uses parameterized queries by default (safe)
│   ├── Never use raw SQL strings with user input
│   └── Validate UUIDs match UUID format before DB queries
└── General
    ├── Max length enforcement (question: 500 chars, name: 100 chars)
    ├── Strip null bytes and control characters
    └── Normalize unicode (prevent homoglyph attacks)
```

### Layer 4: Authentication & Authorization

```
Supabase Auth handles:
├── Password hashing (bcrypt, server-side)
├── JWT token issuance and validation
├── OAuth flow (Google, Apple)
├── Email verification
└── Rate limiting on auth endpoints (Supabase built-in)

Our backend validates:
├── JWT signature verification on every protected request
├── Token expiration check
├── User exists in our database (not just in Supabase Auth)
├── User owns the resource they're accessing (no IDOR)
└── Premium features require active subscription (server-verified)
```

### Layer 5: Data Protection

```
Secrets Management:
├── All secrets in .env file (never committed to git)
├── .env.example with placeholder values (committed)
├── Supabase service_role key ONLY on backend (never in Flutter)
├── Gemini API key ONLY on backend
└── RevenueCat webhook secret ONLY on backend

Database Security:
├── Row Level Security (RLS) enabled on all tables
├── Users can only read/write their own data
├── Service role key used only for admin operations
├── Connection via Session Pooler (port 5432, IPv4)
└── SSL/TLS enforced on all database connections

Data Privacy:
├── Minimal data collection (only what's needed)
├── Birth time and city are optional
├── No tracking or analytics SDKs in MVP
└── GDPR-ready: users can delete their account and all data
```

### Layer 6: Third-Party API Security

```
Gemini API:
├── API key stored server-side only
├── User input sanitized before sending to Gemini
├── Response validated before returning to user
├── Timeout: 30 seconds max
├── Fallback responses when Gemini is unavailable
└── No user PII sent to Gemini (only zodiac sign, cards, anonymized question)

RevenueCat Webhooks:
├── Signature verification on every webhook (X-RevenueCat-Signature)
├── Reject webhooks with invalid signatures (401)
├── Process webhooks idempotently (handle duplicate events)
└── Respond 200 quickly, process in background
```

### Security Testing Checklist (Step 6)

```
Automated (in CI/CD):
├── bandit: Static analysis for Python security issues
├── safety: Check dependencies for known vulnerabilities
├── ruff: Catch common coding errors
└── Custom tests: XSS, SQLi, prompt injection, JWT manipulation

Manual (before each release):
├── OWASP Top 10 review
├── Dependency audit (pip audit)
├── Secret scanning (no keys in git history)
└── API endpoint review (no unprotected routes)
```

### Security Documentation for Portfolio

Create `SECURITY.md` at project root documenting:
- Threat model (what could go wrong)
- Security controls per layer
- Incident response plan (what to do if compromised)
- Dependency update policy

---

## 🎨 Visual Design & Assets

### Tarot Card Art (78 cards)

**Tool:** Google ImageFX (AI image generation)
**Style:** Consistent mystical/esoteric art style across all 78 cards

```
Production Pipeline:
1. Create a style reference prompt for consistent look
   Example: "Mystical tarot card illustration, dark background with
   gold accents, art nouveau style borders, detailed symbolism,
   high quality, consistent art style"
2. Generate 22 Major Arcana cards first (most visible)
3. Generate 56 Minor Arcana (14 per suit: Wands, Cups, Swords, Pentacles)
4. Generate card back design (one universal back)
5. Export at 2x resolution for retina displays
6. Optimize with TinyPNG/WebP for mobile performance

File Structure:
assets/images/tarot/
├── major/
│   ├── 00_the_fool.webp
│   ├── 01_the_magician.webp
│   └── ... (22 cards)
├── minor/
│   ├── wands/
│   ├── cups/
│   ├── swords/
│   └── pentacles/
├── card_back.webp
└── card_placeholder.webp

Specs:
├── Format: WebP (50-70% smaller than PNG)
├── Resolution: 750x1294 px (standard tarot ratio 1:1.73)
├── Max file size: 150KB per card
└── Total deck size target: < 12MB
```

### Animation Strategy

**Approach:** Lottie for pre-made animations + Custom Flutter for particles

```
Lottie Animations (pre-made, lightweight):
├── Card flip animation (front ↔ back)
├── Card reveal glow effect
├── Loading spinner (cosmic theme)
├── Success celebration (stars burst)
├── Onboarding transitions
└── Zodiac wheel rotation

Source: LottieFiles.com (free tier has mystical/cosmic animations)
Package: lottie (Flutter package)
File format: .json (typically 10-50KB per animation)

Custom Flutter Particles:
├── Starfield background (floating stars on dark background)
├── Cosmic dust effect (subtle particles on home screen)
├── Card selection sparkle trail
└── Mystic energy flow between cards during reading

Package: flutter_particles or custom with Canvas API
Performance: Use RepaintBoundary to isolate particle layers

Implementation Rules:
├── All animations run at 60fps minimum
├── Particle effects use GPU-accelerated Canvas
├── Lottie files loaded lazily (not all at startup)
├── Animations respect "reduce motion" accessibility setting
├── Battery-conscious: reduce particles when battery < 20%
└── Test on oldest supported device (iPhone SE 2nd gen / budget Android)
```

### Theme Constants

```dart
// colors.dart
class CosmoColors {
  static const background = Color(0xFF0A0A1A);     // Deep navy black
  static const primary = Color(0xFFC9A84C);         // Mystic gold
  static const secondary = Color(0xFF7B2FBE);       // Purple
  static const accent = Color(0xFFE8D5B7);          // Cream/parchment
  static const textPrimary = Color(0xFFF0E6D3);     // Warm white
  static const textSecondary = Color(0xFF8E8E93);   // Muted gray
  static const error = Color(0xFFE74C3C);           // Soft red
  static const success = Color(0xFF2ECC71);         // Emerald
  static const cardBorder = Color(0xFF2A2A3E);      // Subtle border
  static const gradientTop = Color(0xFF1A1A2E);     // Gradient dark
  static const gradientBottom = Color(0xFF0A0A1A);  // Gradient darker
}

// Fonts: Cinzel (serif, titles) + Lato (sans-serif, body)
// Both available on Google Fonts (free, open source)
```

---

## 🗺️ Development Phases (8 Steps)

### Overview

| Step | Name | Description | Est. Time |
|------|------|-------------|-----------|
| 1 | Project Setup & Database | Supabase, models, migrations, .env | 1 day |
| 2 | Authentication | Google + Apple + Email sign-in, JWT, protected routes | 1-2 days |
| 3 | Core Services | Tarot engine, numerology, astrology, horoscope logic | 2-3 days |
| 4 | AI Integration | Gemini API, prompt engineering, fallbacks | 1-2 days |
| 5 | API Endpoints | All REST endpoints, rate limiting, input validation | 1-2 days |
| 6 | QA Strategy | Tests (unit/integration/contract), CI/CD, security | 2-3 days |
| 7 | Frontend Flutter | Onboarding, home, readings, animations | 5-7 days |
| 8 | Payments (RevenueCat) | Subscriptions, webhooks, paywall | 2-3 days |

**Total estimated: 15-23 days**

---

## 📦 STEP 1 — Project Setup & Database Schema

### Goal
Set up the project structure, connect to Supabase PostgreSQL, and create all database models.

### Tasks

**1.1 — Project structure**
```
cosmotarot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings with pydantic-settings
│   │   ├── api/                 # Route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── tarot.py
│   │   │   ├── horoscope.py
│   │   │   └── webhooks.py
│   │   ├── models/              # SQLModel database models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── reading.py
│   │   │   ├── subscription.py
│   │   │   └── compatibility.py
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── tarot.py
│   │   │   └── horoscope.py
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── tarot.py
│   │   │   ├── numerology.py
│   │   │   ├── astrology.py
│   │   │   ├── ai.py
│   │   │   └── limits.py
│   │   ├── security/            # Input sanitization, rate limiting
│   │   │   ├── __init__.py
│   │   │   └── sanitizer.py
│   │   └── db/
│   │       ├── __init__.py
│   │       └── database.py      # Engine, session, connection
│   ├── tests/
│   │   ├── conftest.py          # SHARED fixtures (one engine, one override)
│   │   ├── unit/
│   │   ├── integration/
│   │   └── contract/
│   ├── alembic/                 # Database migrations
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   ├── .env.example
│   └── CLAUDE.md                # Claude Code project context
├── frontend/                    # Flutter app (Step 7)
├── .github/
│   └── workflows/
│       └── qa-pipeline.yml
├── .gitignore
├── QA_STRATEGY.md
└── README.md
```

**1.2 — Database models (SQLModel)**

```
Table: users
├── id: UUID (PK, auto-generated)
├── email: str (unique, required)
├── full_name: str (required)
├── auth_provider: str ("google" | "apple" | "email")
├── birth_date: date (required — for life number + zodiac)
├── birth_time: time (optional — for full natal chart)
├── birth_city: str (optional)
├── birth_country: str (optional)
├── latitude: float (optional, calculated)
├── longitude: float (optional, calculated)
├── zodiac_sign: str (calculated from birth_date)
├── life_number: int (calculated from birth_date)
├── onboarding_answers: JSON
├── preferred_language: str (default: "es")
├── timezone: str (default: "America/Mexico_City")
├── is_premium: bool (default: false)
├── created_at: datetime (auto)
└── updated_at: datetime (auto)

Table: daily_readings
├── id: UUID (PK)
├── user_id: UUID (FK → users)
├── reading_date: date
├── cards_drawn: JSON (list of 3 cards with position + orientation)
├── ai_interpretation: text
├── spread_type: str ("past_present_future" | "situation_action_outcome")
├── language: str ("es" | "en")
├── created_at: datetime (auto)
└── UNIQUE(user_id, reading_date)  # One reading per day

Table: tarotist_questions
├── id: UUID (PK)
├── user_id: UUID (FK → users)
├── question: text
├── answer: text (AI-generated)
├── category: str ("love" | "career" | "personal" | "spiritual")
├── is_free: bool
├── language: str
├── asked_at: datetime (auto)

Table: subscriptions
├── id: UUID (PK)
├── user_id: UUID (FK → users, unique)
├── plan: str ("free" | "premium_monthly" | "premium_annual")
├── revenue_cat_id: str (nullable)
├── started_at: datetime
├── expires_at: datetime (nullable)
├── is_active: bool (default: true)
├── created_at: datetime (auto)
└── updated_at: datetime (auto)

Table: compatibility_readings
├── id: UUID (PK)
├── user_id: UUID (FK → users)
├── partner_zodiac: str
├── partner_birth_date: date (optional)
├── ai_interpretation: text
├── compatibility_score: int (1-100)
├── language: str
├── created_at: datetime (auto)
```

**1.3 — Environment variables needed**
```
DATABASE_URL=postgresql://...  (Session Pooler, port 5432)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
GEMINI_API_KEY=...
REVENUECAT_WEBHOOK_SECRET=...  (Step 8)
```

**1.4 — Key Python packages**
```
# requirements.txt (production)
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
sqlmodel>=0.0.22
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0
supabase>=2.9.0
google-generativeai>=0.8.0
pydantic[email]>=2.9.0
pydantic-settings>=2.5.0
slowapi>=0.1.9
alembic>=1.13.0

# requirements-dev.txt (testing + linting)
-r requirements.txt
pytest>=8.3.0
pytest-cov>=5.0.0
httpx>=0.27.0
pytest-mock>=3.14.0
ruff>=0.6.0
bandit>=1.7.0
safety>=3.2.0
```

### Verification Checklist
- [ ] `uvicorn app.main:app --reload` starts without errors
- [ ] Swagger UI at http://127.0.0.1:8000/docs loads
- [ ] Health check endpoint returns 200
- [ ] Database connection test passes (Supabase PostgreSQL)
- [ ] All tables created in Supabase (verify in Dashboard → Table Editor)
- [ ] Alembic migration runs successfully

---

## 🔐 STEP 2 — Authentication System

### Goal
Implement Google + Apple + Email authentication using Supabase Auth with JWT token validation.

### Tasks

**2.1 — Auth endpoints**
```
POST /api/auth/register       → Email + password + profile data
POST /api/auth/login          → Email + password → JWT
POST /api/auth/social         → Google/Apple OAuth token → JWT
POST /api/auth/logout         → Invalidate session
POST /api/auth/refresh        → Refresh JWT token
GET  /api/auth/me             → Get authenticated user profile
PUT  /api/auth/profile        → Update profile data
```

**2.2 — Supabase Auth configuration**
- Enable Email provider (Confirm email OFF for dev, ON for production)
- Enable Google OAuth provider
- Enable Apple OAuth provider
- "Allow new users to sign up" → ON

**2.3 — JWT middleware**
- Create `get_current_user` dependency that validates JWT against Supabase
- Protect all endpoints except /register, /login, /social, /health

**2.4 — Onboarding questions (stored in onboarding_answers JSON)**
```
1. "What area of your life seeks guidance?"
   → Options: love, career, personal, spiritual

2. "How should your tarotist speak to you?"
   → Options: direct, reflective, poetic

3. "How do you view destiny?"
   → Options: everything_is_written, you_decide, balance
```

**2.5 — Rate limiting**
- POST /api/auth/login: max 5 attempts per 15 minutes per IP
- POST /api/auth/register: max 3 per hour per IP

### Verification Checklist
- [ ] POST /register with email returns 200 + user_id
- [ ] User appears in Supabase Dashboard → Authentication → Users
- [ ] User appears in Database → users table
- [ ] POST /login returns JWT access_token + refresh_token
- [ ] GET /me with valid JWT returns user profile
- [ ] GET /me without token returns 401
- [ ] PUT /profile updates user data correctly
- [ ] POST /refresh returns new access_token
- [ ] Duplicate email registration returns 409
- [ ] Wrong password login returns 401

---

## 🃏 STEP 3 — Core Services (Business Logic)

### Goal
Build the tarot engine, numerology calculator, astrology service, and horoscope logic — all as pure Python functions with no external dependencies (easy to test).

### Tasks

**3.1 — Tarot Service (`services/tarot.py`)**
- Full 78-card Rider-Waite deck (22 Major + 56 Minor Arcana)
- Each card: name, arcana, suit, number, meaning_upright, meaning_reversed, keywords
- Draw function: randomly select N cards, each with upright/reversed orientation
- No repeated cards in a single spread
- Spread types: past_present_future, situation_action_outcome

**3.2 — Numerology Service (`services/numerology.py`)**
- Life number calculation (reduce birth date to single digit or master number 11/22/33)
- Personal year number
- Personal month number
- Meanings for numbers 1-9 + master numbers

**3.3 — Astrology Service (`services/astrology.py`)**
- Zodiac sign calculation from birth date
- Zodiac sign characteristics (element, ruling planet, compatible signs)
- Daily horoscope generation (AI-assisted)
- Compatibility calculator between two zodiac signs (element harmony, traditional compatibility)

**3.4 — Data files (`data/`)**
- `tarot_deck.json`: Complete 78-card deck with bilingual meanings (es/en)
- `zodiac_signs.json`: 12 signs with characteristics
- `life_numbers.json`: Numbers 1-9 + 11, 22, 33 with meanings

### Verification Checklist
- [ ] Tarot draw returns exactly 3 unique cards
- [ ] Each card has all required fields
- [ ] Life number calculated correctly for 5+ known cases
- [ ] Zodiac sign correct for edge cases (cusp dates)
- [ ] Compatibility score returns value between 1-100

---

## 🤖 STEP 4 — AI Integration (Gemini)

### Goal
Integrate Google Gemini to generate personalized tarot interpretations, horoscopes, and compatibility readings.

### Tasks

**4.1 — AI Service (`services/ai.py`)**
- Initialize Gemini client with API key
- System prompt that adapts personality based on user's onboarding_answers
- Generate tarot interpretation from cards + user context
- Generate daily horoscope based on zodiac sign
- Generate compatibility analysis
- Fallback responses when Gemini is unavailable

**4.2 — Prompt engineering**
- System prompt template with user personality variables
- Tarot reading prompt: cards drawn + positions + user's question + language
- Horoscope prompt: zodiac sign + current date + language
- Compatibility prompt: two signs + element analysis + language
- All prompts bilingual (es/en)

**4.3 — Error handling**
- 429 Rate Limit → retry with exponential backoff
- 503 Service Unavailable → use cached/fallback response
- Timeout → use fallback ("The stars are silent right now...")
- Empty response → use generic positive interpretation

**4.4 — Input sanitization (BEFORE sending to AI)**
- XSS prevention: escape HTML in user questions
- Prompt injection detection: block "ignore instructions" patterns
- Max question length: 500 characters

### Verification Checklist
- [ ] Gemini returns interpretation for a 3-card spread
- [ ] Response adapts to user's preferred style (direct/reflective/poetic)
- [ ] Response is in the correct language (es/en)
- [ ] Fallback works when Gemini is mocked as unavailable
- [ ] Prompt injection attempt is blocked
- [ ] XSS input is escaped before reaching Gemini

---

## 🌐 STEP 5 — API Endpoints

### Goal
Wire up all REST endpoints connecting auth, services, and AI.

### Tasks

**5.1 — Tarot endpoints**
```
GET  /api/tarot/daily         → Get today's 3-card reading (creates if not exists)
POST /api/tarot/ask           → Ask the AI tarotist a question (free: 1/day)
GET  /api/tarot/history       → Get past readings (free: 7 days, premium: all)
```

**5.2 — Horoscope endpoints**
```
GET  /api/horoscope/daily     → Daily horoscope for user's zodiac sign
GET  /api/horoscope/weekly    → Weekly overview (premium)
```

**5.3 — Numerology endpoints**
```
GET  /api/numerology/profile  → Life number + personal year + personal month
```

**5.4 — Compatibility endpoints**
```
POST /api/compatibility/check → Check compatibility with a partner's sign/date
GET  /api/compatibility/history → Past compatibility readings (premium)
```

**5.5 — User limits service**
```python
check_user_limits(user_id) → {
    can_read: bool,
    can_ask: bool,
    readings_today: int,
    questions_today: int,
    is_premium: bool
}
```

### Verification Checklist
- [ ] All endpoints appear in Swagger with correct methods
- [ ] Protected endpoints return 401 without token
- [ ] Free user gets blocked after daily limit
- [ ] Premium user has no limits
- [ ] Same-day /tarot/daily returns cached reading (not new one)
- [ ] /tarot/ask with empty question returns 422 validation error

---

## 🧪 STEP 6 — QA Strategy (Tests + CI/CD + Security)

### Goal
Build a comprehensive test suite that serves as a QA portfolio piece. Every test has a docstring explaining WHAT it tests and WHY.

### THIS IS THE MOST IMPORTANT STEP FOR YOUR PORTFOLIO

### Tasks

**6.1 — Test infrastructure**
- `tests/conftest.py`: ONE shared test engine, fixtures, mock authenticated user
- PostgreSQL for integration tests (Docker container in CI, Supabase test DB locally)
- No SQLite — we test against real PostgreSQL to catch real bugs
- pytest-cov for coverage (target: ≥ 85%)

**6.2 — Unit tests (`tests/unit/`)**
```
test_tarot_service.py
├── test_draw_returns_exactly_3_cards
├── test_no_repeated_cards_in_spread
├── test_each_card_has_required_fields
├── test_card_orientation_is_upright_or_reversed
└── test_full_deck_has_78_cards

test_numerology_service.py
├── test_life_number_known_cases (5+ cases)
├── test_master_numbers_not_reduced (11, 22, 33)
├── test_personal_year_calculation
└── test_invalid_date_raises_error

test_astrology_service.py
├── test_zodiac_sign_all_12_signs
├── test_zodiac_cusp_dates
├── test_compatibility_score_range
└── test_same_sign_compatibility

test_limits_service.py
├── test_free_user_can_read_once
├── test_free_user_blocked_after_limit
├── test_premium_user_unlimited
└── test_limit_resets_at_midnight

test_sanitizer.py
├── test_xss_input_escaped
├── test_prompt_injection_blocked
├── test_clean_input_passes_through
└── test_max_length_enforced
```

**6.3 — Integration tests (`tests/integration/`)**
```
test_auth_endpoints.py
├── test_register_creates_user
├── test_register_duplicate_email_409
├── test_login_returns_jwt
├── test_login_wrong_password_401
├── test_me_with_valid_token
├── test_me_without_token_401
├── test_profile_update
└── test_refresh_token

test_tarot_endpoints.py
├── test_daily_reading_creates_new
├── test_daily_reading_returns_cached
├── test_ask_tarotist_free_user
├── test_ask_tarotist_limit_exceeded_free
├── test_ask_tarotist_unlimited_premium
└── test_history_pagination

test_compatibility_endpoints.py
├── test_check_compatibility_returns_score
├── test_compatibility_requires_premium
└── test_compatibility_with_invalid_sign

test_security_integration.py
├── test_sql_injection_attempt_on_profile
├── test_xss_in_tarot_question
├── test_manipulated_jwt_rejected
├── test_expired_token_rejected
└── test_rate_limit_on_login
```

**6.4 — Contract tests (`tests/contract/`)**
```
test_gemini_contract.py
├── test_successful_interpretation
├── test_rate_limit_429_uses_fallback
├── test_service_unavailable_503_uses_fallback
├── test_timeout_uses_fallback
├── test_empty_response_uses_fallback
└── test_malformed_response_handled
```

**6.5 — CI/CD Pipeline (`.github/workflows/qa-pipeline.yml`)**
```yaml
Triggers: push to any branch, PR to main
Steps:
  1. Setup Python 3.12
  2. Install dependencies
  3. Linting: ruff check
  4. Security scan: bandit + safety
  5. Unit tests with coverage
  6. Integration tests (PostgreSQL service container)
  7. Contract tests
  8. Upload coverage to Codecov
  9. Fail pipeline if coverage < 85%
```

**6.6 — QA_STRATEGY.md**
- Comprehensive document for portfolio
- Testing pyramid diagram
- Tools and rationale for each
- How to run each test tier
- Coverage metrics and quality gates
- Security measures documented

### Verification Checklist
- [ ] `pytest tests/unit/ -v` → all green
- [ ] `pytest tests/integration/ -v` → all green
- [ ] `pytest tests/contract/ -v` → all green
- [ ] `pytest --cov=app --cov-report=term-missing` → ≥ 85%
- [ ] `ruff check app/ tests/` → 0 errors
- [ ] `bandit -r app/ -ll` → 0 high/medium issues
- [ ] GitHub Actions pipeline runs green on push
- [ ] No flaky tests (run suite 3x, all pass every time)

---

## 📱 STEP 7 — Frontend Flutter

### Goal
Build a mystical, visually stunning mobile app with smooth animations.

### Tasks

**7.1 — Screens**
```
SplashScreen        → Animated starfield + logo fade-in
OnboardingFlow      → 5-step registration with PageView
├── Step 1: Welcome ("Welcome to the cosmos")
├── Step 2: Personal data (name, email, password, birth date)
├── Step 3: Astrological data (optional: birth time, city)
├── Step 4: 3 onboarding questions (card flip animation)
└── Step 5: Your life number (rolling number animation)
HomeScreen          → Daily reading + horoscope + quick actions
TarotReadingScreen  → 3 cards face-down → flip animation → interpretation
HoroscopeScreen     → Daily horoscope with zodiac wheel
CompatibilityScreen → Select partner sign → animated result
ProfileScreen       → User data + subscription status
PaywallScreen       → Free vs Premium comparison
```

**7.2 — Visual theme**
```
Background:  #0A0A1A (deep navy black)
Primary:     #C9A84C (mystic gold)
Secondary:   #7B2FBE (purple)
Accent:      #E8D5B7 (cream/parchment)
Text:        #F0E6D3 (warm white)
Fonts:       Cinzel (serif, titles) + Lato (sans-serif, body)
```

**7.3 — Architecture**
- Riverpod for state management
- go_router for navigation
- flutter_secure_storage for JWT
- Dio for HTTP client
- i18n with flutter_localizations (es + en from day one)

### Verification Checklist
- [ ] App builds for iOS and Android
- [ ] Onboarding flow completes and creates user
- [ ] Daily reading displays 3 cards with flip animation
- [ ] Horoscope shows for user's zodiac sign
- [ ] All text appears in correct language
- [ ] JWT stored securely and refreshed automatically

---

## 💳 STEP 8 — Payments (RevenueCat)

### Goal
Implement subscription management with RevenueCat.

### Tasks

**8.1 — Backend: Webhook handler**
```
POST /webhooks/revenuecat → Verify signature, handle events:
├── INITIAL_PURCHASE  → Activate premium
├── RENEWAL           → Extend expiration
├── CANCELLATION      → Mark as cancelled (access until expires_at)
└── EXPIRATION        → Deactivate premium
```

**8.2 — Flutter: Subscription service**
- Initialize RevenueCat SDK
- Get offerings (monthly $4.44 / annual $44.44)
- Purchase flow
- Restore purchases
- Check entitlements

**8.3 — Paywall screen**
- Free vs Premium comparison
- Numerology-themed pricing display
- "Cancel anytime" messaging
- Restore purchases option

### Verification Checklist
- [ ] Webhook receives test event and updates subscription
- [ ] Invalid webhook signature returns 401
- [ ] Free → Premium transition unlocks all features
- [ ] Premium → Expired removes access
- [ ] Paywall displays correct prices
- [ ] Restore purchases works

---

## 🐛 Bug Tracking Rules

Every bug gets documented in `BUG_LEDGER.md` with:
```
## Bug XX: [Short title]
- **Date:** YYYY-MM-DD
- **Symptom:** What happened
- **Root cause:** Why it happened
- **Fix:** What we changed
- **Lesson:** What we learned
- **Status:** RESOLVED / OPEN
```

---

## ⚡ Development Rules (IMPORTANT)

1. **Never skip verification.** Each step's checklist must be 100% green before moving on.
2. **Test through the actual interface.** Code review alone is NOT verification — run the server, hit Swagger, see the 200.
3. **Use PostgreSQL everywhere.** No SQLite for testing. Ever.
4. **One shared conftest.py.** One test engine, one set of fixtures, one dependency override.
5. **Pydantic V2 syntax only.** Use `model_dump()` not `dict()`, `datetime.now(UTC)` not `datetime.utcnow()`.
6. **Every test has a docstring.** Explain WHAT and WHY.
7. **Commit after each verified step.** Clean git history.
8. **English for code, Spanish for user-facing content.**
9. **No secrets in Flutter.** All API keys live on the backend only.
10. **Sanitize ALL user inputs.** Every string from the user goes through the sanitizer before processing.
11. **Rate limit ALL public endpoints.** No endpoint should be callable unlimited times.
12. **Animations respect accessibility.** Always check "reduce motion" system setting.

---

## 📊 Scalability Plan

| Users | Database | AI Calls | Hosting | Monthly Cost |
|-------|----------|----------|---------|-------------|
| 0-500 | Supabase Free | Gemini Free Tier | Supabase Free | $0 |
| 500-5K | Supabase Pro | Gemini Pay-as-go | Supabase Pro | ~$30-50 |
| 5K-50K | Supabase Pro + cache | Gemini + response caching | + CDN | ~$100-200 |
| 50K+ | Own PostgreSQL (AWS/GCP) | Multi-model fallback | Kubernetes | Negotiate |

**Key architectural decisions for scalability:**
- Cache daily horoscopes (same for all users of same sign)
- Cache daily readings per user (one read per day)
- Response caching for AI calls with similar prompts
- Database connection pooling from day one (Supabase Session Pooler)
- Stateless JWT auth (no session storage needed)

---

## 🔮 Future Expansion (Post-MVP)

- Asian expansion: Saju, Chinese Lunar Calendar, I Ching
- Tarot journal (save and annotate readings)
- Ask the Tarotist (chat-style AI Q&A)
- Push notifications (daily reading reminder)
- Widgets (iOS/Android home screen)
- Web version (Flutter web)
- Community features (share readings)

---

## 📁 Portfolio Documents (generated during development)

These documents make CosmoTarot a showcase project:

| Document | Purpose | Created in Step |
|----------|---------|-----------------|
| `README.md` | Project overview, setup instructions, architecture | Step 1 |
| `CLAUDE.md` | Claude Code project context | Step 1 |
| `QA_STRATEGY.md` | Testing pyramid, tools, metrics, quality gates | Step 6 |
| `SECURITY.md` | Threat model, security controls, incident response | Step 6 |
| `BUG_LEDGER.md` | Every bug documented with root cause and fix | Ongoing |
| `API_DOCS.md` | Full API reference (auto-generated from Swagger) | Step 5 |

---

*This roadmap is designed to be used with Claude Code in the terminal. Each step is self-contained with clear inputs, outputs, and verification checklists. Build one step at a time, verify completely, commit, then move to the next.*