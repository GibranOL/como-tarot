# Bug Ledger — CosmoTarot

Every bug found during development is documented here with root cause and lesson learned.

---

## Bug 01: FK Violation on Daily Reading / Compatibility Insertion

- **Date:** 2026-03-12
- **Symptom:** Integration tests for `/api/tarot/daily`, `/api/tarot/ask`, and `/api/compatibility/check` failed with `psycopg2.errors.ForeignKeyViolation: insert or update on table "daily_readings" violates foreign key constraint "daily_readings_user_id_fkey"` when run against a real PostgreSQL database.
- **Root cause:** Test fixtures injected a `User` object in-memory via `get_current_user` dependency override, but never inserted that user into the `users` table. When the endpoint persisted a `DailyReading` or `CompatibilityReading` with `user_id = <mock_uuid>`, PostgreSQL rejected it because no matching row existed in `users`. SQLite (previously used for tests) silently ignores foreign key constraints by default, so this bug was invisible until PostgreSQL was introduced.
- **Fix:** Added `db_session.add(user); db_session.commit(); db_session.refresh(user)` to all integration test fixtures (`client_fixture`, `premium_client_fixture`, `free_client_fixture`, `auth_client_fixture`) before yielding the `TestClient`. The mock user is now a real DB row for the duration of each test.
- **Lesson:** SQLite's permissive FK handling creates a false sense of security. This is exactly why the project rule says "No SQLite for testing. Ever." — a test suite that passes on SQLite may still produce FK violations in production PostgreSQL. Always test against the same database engine you run in production.
- **Status:** RESOLVED

---

## Bug 02: UniqueViolation on User Email Across Tests

- **Date:** 2026-03-12
- **Symptom:** After fixing Bug 01, several integration tests began failing with `psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint "ix_users_email"`. The second and subsequent tests in a session that shared the same test DB would fail during fixture setup.
- **Root cause:** All test fixtures used hard-coded email addresses (e.g., `"test@cosmo.mx"`, `"compat-prem@cosmo.mx"`). The test engine is session-scoped (shared across all tests), so committed rows persist between tests. The second test to insert a user with the same email violated the `UNIQUE` constraint on `users.email`.
- **Fix:** Changed `_make_user()` helpers in all integration test files to generate a unique email per call, derived from the user's UUID: `email=f"tarot-{uid.hex[:8]}@cosmo.mx"`. Since the UUID is random for each `_make_user()` invocation, email collisions are statistically impossible.
- **Lesson:** When using a session-scoped test database, any data committed by one test is visible to all subsequent tests. Fixtures that create DB rows must use unique identifiers — do not rely on hard-coded strings for fields with `UNIQUE` constraints. This pattern (UUID-derived emails) should be the default for any fixture that inserts users.
- **Status:** RESOLVED

---

## Bug 03: Missing Input Sanitization on `/api/tarot/ask` Endpoint

- **Date:** 2026-03-12
- **Symptom:** Security integration tests for prompt injection (e.g., `"Ignore previous instructions..."`) expected a `400 Bad Request` response from the API but received `201 Created`. XSS payloads like `<script>alert('xss')</script>` were passed unsanitized to the AI service and stored in the database.
- **Root cause:** The `ask_tarotist` endpoint passed `req.question` (the raw, unsanitized user input) directly to `answer_tarotist_question()`. The `sanitize_input()` function existed in `app/security/sanitizer.py` and was used inside the AI service as a fallback, but was never called at the endpoint boundary. CLAUDE.md Layer 3 explicitly requires: *"All user text inputs pass through sanitizer BEFORE processing."* This boundary-level call was missing.
- **Fix:** Added an explicit `sanitize_input(req.question)` call at the start of `ask_tarotist()` before any business logic. A `SanitizationError` (raised on detected prompt injection or XSS) is caught and converted to `HTTP 400 Bad Request`. The sanitized string is then passed to `answer_tarotist_question()` and stored in the `TarotistQuestion` record.
- **Lesson:** Defense-in-depth requires sanitization at the **API boundary**, not just inside internal services. Having a sanitizer that is only called conditionally or deep in the call stack creates a gap: future refactors may bypass it entirely. The correct pattern is: *sanitize at the controller layer before any service call*, so the contract is impossible to accidentally skip.
- **Status:** RESOLVED

---

## Bug 04: Login y Registro Redirigen al Login en Lugar de Home

- **Date:** 2026-03-13
- **Symptom:** Al completar el registro de un nuevo usuario o al iniciar sesión con uno existente, la app redirigía de vuelta a la pantalla de login en lugar de navegar a la pantalla principal (home).
- **Root cause:** El router (`routerProvider` en `app_router.dart`) observaba `authStateProvider` (un `FutureProvider`) para determinar si el usuario estaba autenticado. Sin embargo, las pantallas de login y registro llamaban a `authNotifierProvider` (un `AsyncNotifierProvider`) para ejecutar las acciones de autenticación. Al ser dos providers independientes, cuando `authNotifierProvider` se actualizaba con el usuario autenticado, `authStateProvider` nunca se invalidaba ni notificaba al router. El router seguía viendo `valueOrNull == null` (no autenticado) y su redirect sobreescribía el `context.go(AppRoutes.home)` enviando al usuario de vuelta al login.
- **Fix:** Se cambió el router para que observe `authNotifierProvider` en lugar de `authStateProvider` (`app_router.dart` línea 33). Con esto, el router reconstruye y evalúa el redirect cada vez que login o registro actualizan el estado de auth. Adicionalmente se extendió el redirect automático a home para cubrir también la ruta `/register`, no solo `/login`.
- **Lesson:** En una arquitectura Riverpod, el router debe observar exactamente el mismo provider que las pantallas de auth actualizan. Tener dos providers que representan "el usuario autenticado" es una duplicación peligrosa: uno puede cambiar sin que el otro se entere. La regla: un solo provider de verdad para el estado de auth, y todos los consumidores (router, pantallas, widgets) lo observan desde ahí.
- **Status:** RESOLVED
