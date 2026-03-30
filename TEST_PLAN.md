# Booma test plan

Scope covers the **local prototype** (`services/` + `front-end/`) and future increments toward full production.

## 1. API smoke tests (automated)

Implemented under `services/tests/test_api_smoke.py`, `test_pricing.py`, and `test_auth_jwt.py`. Run `cd services && pytest` (uses a **temporary** SQLite file via `conftest.py`, not `data/booma.db`).

| Test | Steps | Expected |
|------|--------|----------|
| Health | `GET /health` | `200`, JSON includes `status: ok`, `storage: sqlite` |
| Lifespan | Use `with TestClient(app) as c:` (not a bare `TestClient`) | Tables exist and seed runs on empty DB |
| Login | `POST /api/v1/auth/login` with seeded passenger email + `demo` | `200`, `access_token`, `expires_in` |
| Bad login | Wrong password | `401`, no token |
| Me | `GET /api/v1/users/me` with `Authorization: Bearer` | `200`, profile matches seed |
| Saved addresses | `GET /api/v1/users/saved-addresses` | `200`, list scoped to user |
| List bookings | `GET /api/v1/bookings` as passenger | `200`, only that passenger’s rides |
| Estimate | `GET /api/v1/bookings/estimate` with query coords | `200`, `vehicles`, `distance_km`, `stub_note` |
| Create booking | `POST /api/v1/bookings` with valid body | `201`, `status` is `SEARCHING` |
| Stub maps | `GET /api/v1/stub/maps/autocomplete?q=sydney` | `200`, non-empty list when landmarks match |
| Stub payment | `POST /api/v1/stub/payments/setup-intent` | `200`, fake `payment_intent_id` / `client_secret` |
| AuthZ | `GET /api/v1/bookings/{other_user_ride_id}` | `404` |

**Implementation note:** Starlette’s `TestClient` requires the **`httpx`** package. Lifespan (create tables + seed) runs when entering the `TestClient` context manager.

## 2. API unit tests (Python)

- **pricing:** `haversine_km`, `fare_aud`, `surge_for_prototype` — known inputs/outputs.
- **auth:** JWT payload contains `sub`, `role`, `exp`; expired token rejected.
- **booking state:** When a state machine is added, test allowed and forbidden transitions (see design `02-architecture-overview.md`).

## 3. Front-end (manual / E2E)

| Area | Check |
|------|--------|
| Login | Valid passenger logs in; invalid password shows error |
| Session | Token in `sessionStorage`; refresh page stays logged in |
| Logout | Clears session and returns to login |
| Estimate + book | Actions hit `/api` via Vite proxy (no CORS errors) |
| Stubs | “Test stub maps API” / “Test stub Stripe” update UI or console |
| Table | Ride list shows seeded + new rides |

**Future:** Playwright or Cypress against `npm run start` + `uvicorn`, with API on `127.0.0.1:8000`.

## 4. Security-focused (prototype → production)

| Topic | Prototype | Later |
|--------|-----------|--------|
| JWT secret | Default in settings | Env-only, strong secret, rotation |
| HTTPS | Not required locally | TLS everywhere |
| CSRF | Not modeled for Bearer-only UI | Cookies + CSRF tokens if using refresh cookies |
| Rate limits | None | Per `03-security-architecture.md` tiers |
| IDOR | Bookings checked by `passenger_id` | Extend for drivers/admin |

## 5. Data & migrations

- After schema changes, delete `services/data/booma.db` or add Alembic migrations and re-seed.
- Verify seed idempotency: second startup does **not** duplicate users (count check in `seed_if_empty`).

## 6. Regression checklist (before demos)

- [ ] Backend: `uvicorn app.main:app` from `services/` with venv active.
- [ ] Front-end: from **repository root**, `cd front-end && npm run start`; proxy to API works (`front-end` is next to `services/`, not inside it).
- [ ] `npm run build` succeeds for production assets.
- [ ] Login as `sophie.zhang@gmail.com` / `demo` (or documented env password).

---

*Design references for future tests:* ride state machine, WebSocket subscription rules, and payment idempotency in `references/designs/02-architecture-overview.md` and `03-security-architecture.md`.
