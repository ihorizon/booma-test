# Booma implementation roadmap

This roadmap ties the **local prototype** (Aurelia + FastAPI + SQLite + stubs) to the target architecture in `references/designs/`. Each phase lists **context**, **tasks**, **success metrics**, and **tests** so progress can be checked objectively.

---

## Verification log (update when you run checks)

| Check | Command (from repo root unless noted) | Last run | Result |
|--------|----------------------------------------|----------|--------|
| API unit + smoke (18 cases) | `cd services && source .venv/bin/activate && pytest` | 2026-03-30 | **18 passed** |
| Front-end unit smoke | `cd ../front-end && npm test -- --run` **after** `cd services`, **or** `cd front-end && npm test -- --run` from repo root | 2026-03-30 | **1 passed** (class export; see note below) |
| Front-end production build | Same as above with `npm run build` | 2026-03-30 | **Success** (Vite may log parse5 warnings on Aurelia templates; build still completes) |

**Path note:** `front-end/` is a sibling of `services/`, not a child. After `cd services`, use `cd ../front-end`, not `cd front-end`. The [README.md](./README.md) **Automated tests** section has a single chained command that does this correctly.

**Note:** Automated **DOM hydration** of `<my-app>` is not exercised in Vitest (jsdom + Aurelia template pipeline is brittle). Full UI flows stay under manual checks in [TEST_PLAN.md](./TEST_PLAN.md) §3 until Playwright/Cypress is added (Phase A).

**Test locations:** `services/tests/` (`test_api_smoke.py`, `test_pricing.py`, `test_auth_jwt.py`), isolated DB via `services/conftest.py` (`BOOMA_SQLITE_PATH` temp file).

---

## Current state (baseline)

- **Front-end:** `front-end/` — Aurelia 2 + Vite, proxy `/api` → port 8000.
- **API:** `services/` — FastAPI, JWT login, bookings, users, stub maps/payments.
- **Data:** SQLite `services/data/booma.db` for local dev; tests use a **temporary** DB.
- **Stubs:** No Mapbox/Google, Stripe, SMS, or email over the network.

---

## Phase A — Solidify the prototype

**Context:** Make the demo repeatable for others (CI, new developers) and close gaps between the HTML reference UI and the Aurelia app—without committing to paid APIs yet.

| Type | Detail |
|------|--------|
| **Tasks** | Expand pytest toward [TEST_PLAN.md](./TEST_PLAN.md) §4 (rate limits optional mock). Add Playwright smoke: login → estimate → book. Optional `docker-compose` (API + `nginx` static `front-end/dist`). Reduce Vite parse5 noise or document as acceptable. Optional: full Aurelia + jsdom fixture if upstream fixes land. |
| **Metrics** | CI job runs **pytest + vitest + build** on every PR; **0** required checks failing. Cold start: documented “two terminals” flow works in **≤ 5 minutes** on a clean clone (excluding npm/pip download time). |
| **Tests** | `pytest` (all modules under `services/tests/`). `npm test` + `npm run build`. Manual: regression checklist in TEST_PLAN §6. |

---

## Phase B — Real integrations (local or staging)

**Context:** Validate real vendor behaviour before production: maps for UX trust, Stripe for money movement, Postgres for concurrency and migrations.

| Type | Detail |
|------|--------|
| **Tasks** | Mapbox or Google (geocode, directions, static or GL map). Stripe test keys + Elements + webhook forwarding (Stripe CLI / ngrok). PostgreSQL + Alembic; keep SQLite for fast unit tests via `BOOMA_SQLITE_PATH` or testcontainers. Redis for GEO / pub-sub prototype. Feature flags: `USE_STUB_MAPS`, omit `STRIPE_SECRET_KEY` → stubs. |
| **Metrics** | **≥ 95%** of happy-path booking flows succeed in **staging** using real maps + Stripe test cards over **N ≥ 20** scripted runs. API **p95 latency** for `/bookings/estimate` **< 2 s** with real routing (adjust target per region). |
| **Tests** | Contract tests against provider sandboxes (mock HTTP where billing applies). Integration tests with Postgres in CI. E2E: one full book + pay path in staging. |

---

## Phase C — Production-shaped backend

**Context:** Align security and real-time behaviour with `03-security-architecture.md` and `02-architecture-overview.md`: gateway, tokens, WebSockets, events.

| Type | Detail |
|------|--------|
| **Tasks** | Modular monolith **or** split services behind API gateway. Refresh tokens (HttpOnly cookie), RS256 + JWKS, rate limits per gateway table. WebSocket gateway for tracking; Redis Streams or Kafka for ride events. Deploy to target region (e.g. `ap-southeast-2`), secrets manager, structured logging, metrics, tracing. |
| **Metrics** | **99%+** token validation correctness in load test (no mass 401 for valid clients). WebSocket fan-out **p95 < 1 s** from driver update to passenger (design target; measure in staging). **Zero** duplicate captures for same idempotency key in Stripe shadow tests. |
| **Tests** | Security suite: IDOR, token expiry, WS subscribe isolation. Load/k6 or Locust on WS + REST. Chaos or failover drill for single AZ (Phase 1 style). |

---

## Phase D — Scale and compliance

**Context:** Growth, multi-AZ, optional multi-region, and formal assurance (privacy, audits, DR).

| Type | Detail |
|------|--------|
| **Tasks** | HPA / replicas per `04-scaling-strategy.md`. Read replicas, backup/RPO/RTO targets. Privacy Act / GDPR workflows: export, delete. Pen test and dependency/container scanning in release pipeline. |
| **Metrics** | **RTO / RPO** meet documented targets (e.g. RTO < 30 min, RPO < 5 min for DB tier). **99.9%** monthly API availability in production (excluding planned maintenance). Cost within projected band per phase in design doc. |
| **Tests** | DR tabletop + automated restore drill. Compliance checklist tests (data deletion e2e). Annual pen test findings tracked to closure. |

---

## How phases map to design references

| Phase | Primary references |
|-------|-------------------|
| A | `references/UI/booma-booking-portal.html`, `TEST_PLAN.md` |
| B | `02-architecture-overview.md` (external systems), `01-market-research.md` (capabilities) |
| C | `03-security-architecture.md`, `02-architecture-overview.md` (WS, state machine) |
| D | `04-scaling-strategy.md`, `03-security-architecture.md` (infra, audit) |

---

*Synthetic data and UI reference:* `references/data/synthetic-data.json`, `references/designs/*.md`.
