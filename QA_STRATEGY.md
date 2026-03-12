# QA Strategy — CosmoTarot API

**Version:** 1.0
**Date:** March 2026
**Coverage Target:** ≥ 85%
**Pipeline:** GitHub Actions (`.github/workflows/qa-pipeline.yml`)

---

## Testing Pyramid

```
           ┌─────────────────────┐
           │   CONTRACT TESTS    │  ← 3rd-party API contracts
           │      (30 tests)     │     (Gemini AI fallbacks)
           ├─────────────────────┤
           │  INTEGRATION TESTS  │  ← HTTP layer, DB persistence,
           │     (~50 tests)     │     auth, premium gates, security
           ├─────────────────────┤
           │     UNIT TESTS      │  ← Pure business logic
           │     (48+ tests)     │     (tarot, numerology, astrology)
           └─────────────────────┘

Rule: Each layer tests what it owns. Unit tests never hit the network.
      Integration tests never call real Supabase or Gemini.
      Contract tests exercise the AI boundary in isolation.
```

---

## Test Tiers

### 1. Unit Tests (`tests/unit/`)

**Purpose:** Verify pure business logic with no external dependencies.
**Speed:** < 2 seconds for the full suite.
**Database:** None.

| File | Tests | What it covers |
|------|-------|----------------|
| `test_tarot_service.py` | 17 | 78-card deck, draw uniqueness, card structure |
| `test_numerology_service.py` | 13 | Life path, personal year/month, master numbers |
| `test_astrology_service.py` | 18 | All 12 zodiac signs, cusp dates, compatibility scoring |
| `test_sanitizer.py` (unit) | 8 | XSS escaping, prompt injection blocking, length limits |

**How to run:**
```bash
cd backend
pytest tests/unit/ -v
```

---

### 2. Integration Tests (`tests/integration/`)

**Purpose:** Verify the full HTTP stack — routing, Pydantic validation, business logic, DB persistence, auth enforcement, and premium gating.
**Database:** Real PostgreSQL (never SQLite — see [Why PostgreSQL](#why-postgresql)).
**External calls mocked:** `generate_tarot_interpretation`, `generate_daily_horoscope`, `generate_compatibility_analysis`, `create_client` (Supabase auth).

| File | Tests | What it covers |
|------|-------|----------------|
| `test_tarot_endpoints.py` | 10 | Daily reading, caching, ask tarotist, history pagination |
| `test_horoscope_numerology_endpoints.py` | 8 | Daily/weekly horoscope, numerology profile, premium gates |
| `test_compatibility_endpoints.py` | 7 | Compatibility check, premium enforcement, invalid input |
| `test_security_integration.py` | 15 | XSS, prompt injection, JWT tampering, SQL injection, rate limits |

**Prerequisites:**
```bash
export TEST_DATABASE_URL=postgresql://postgres:password@localhost:5432/cosmotarot_test

# Quick local PostgreSQL with Docker:
docker run -d -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=cosmotarot_test \
  postgres:16
```

**How to run:**
```bash
cd backend
pytest tests/integration/ -v
```

---

### 3. Contract Tests (`tests/contract/`)

**Purpose:** Verify that our application behaves correctly at the boundary with the Gemini AI API, covering all failure modes without making real API calls.
**Rationale:** Gemini can fail in many ways (rate limit, timeout, empty response, malformed JSON). We test every path so the app never returns a 500 to users due to an AI failure.

| Scenario | Expected behavior |
|----------|------------------|
| Successful response | Returns AI interpretation |
| Rate limit (429) | Returns pre-written fallback message |
| Service unavailable (503) | Returns pre-written fallback message |
| Timeout (30s exceeded) | Returns "The stars are silent right now..." |
| Empty response | Returns generic positive interpretation |
| Malformed response | Handled gracefully, fallback returned |
| Prompt injection in question | Blocked with `SanitizationError` before reaching Gemini |
| User personality adaptation | `direct` / `reflective` / `poetic` style is applied |

**How to run:**
```bash
cd backend
pytest tests/contract/ -v
```

---

## Running the Full Suite

```bash
cd backend

# All tests with coverage
pytest tests/ -v \
  --cov=app \
  --cov-report=term-missing \
  --cov-fail-under=85

# Individual tiers
pytest tests/unit/        # Fast, no external deps
pytest tests/contract/    # AI boundary tests
pytest tests/integration/ # Requires TEST_DATABASE_URL

# Coverage report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

---

## Tooling

| Tool | Purpose | Config |
|------|---------|--------|
| **pytest** | Test runner | `pytest.ini` |
| **pytest-cov** | Coverage measurement | `--cov=app --cov-fail-under=85` |
| **httpx / TestClient** | HTTP integration testing | FastAPI `TestClient` |
| **pytest-mock** | Mocking external services | `unittest.mock.patch` |
| **ruff** | Fast Python linter | `ruff check app/ tests/` |
| **bandit** | Static security analysis | `bandit -r app/ -ll` |
| **safety** | Dependency CVE scanning | `safety check` |

---

## Why PostgreSQL?

> **Rule:** No SQLite for testing. Ever.

SQLite silently ignores or converts many things that PostgreSQL enforces:

| Behavior | SQLite | PostgreSQL |
|----------|--------|-----------|
| UUID column types | Stores as TEXT | Enforces UUID format |
| `UNIQUE` constraint timing | Sometimes deferred | Enforced immediately |
| `CHECK` constraints | Ignored by default | Enforced |
| Case-sensitive LIKE | Always case-insensitive | Case-sensitive by default |
| `RETURNING` clause | Not always supported | Full support |

Using SQLite in tests could allow bugs that only surface in production PostgreSQL.

---

## Quality Gates

The CI/CD pipeline fails if any of the following are not met:

| Gate | Threshold | Tool |
|------|-----------|------|
| Coverage | ≥ 85% | pytest-cov |
| Linting errors | 0 | ruff |
| High/medium security issues | 0 | bandit |
| Test failures | 0 | pytest |

---

## Test Design Principles

1. **Every test has a docstring.** Format: `WHAT: [what is tested]. WHY: [why it matters].`
2. **One assertion per concept.** Tests fail for one reason, making failures easy to diagnose.
3. **No test depends on another test's side effects.** Tests are independent.
4. **Mock at the boundary, not inside the code under test.** We patch `generate_tarot_interpretation`, not the Gemini SDK internals.
5. **Use unique UUIDs per test.** Prevents state leakage between tests sharing a DB.
6. **Test the negative path.** For every valid input test, there is a test for the invalid case.

---

## CI/CD Pipeline

Defined in `.github/workflows/qa-pipeline.yml`.

```
Trigger: push to any branch, PR to main

Steps:
  1. Checkout
  2. Python 3.12 setup + pip cache
  3. Install requirements-dev.txt
  4. ruff check (linting)
  5. bandit (security scan)
  6. safety check (CVE scan)
  7. Unit tests + coverage
  8. Contract tests + coverage (append)
  9. Integration tests + coverage (append, PostgreSQL service container)
 10. Coverage gate ≥ 85%
 11. Upload to Codecov
```

---

*This document is part of the CosmoTarot portfolio. It demonstrates professional QA practices applicable to any production Python/FastAPI project.*
