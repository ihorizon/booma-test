# Booma (prototype)

Local ride-booking prototype: **Aurelia** SPA (`front-end/`) and **Python FastAPI** API (`services/`) using **SQLite** and **stubbed** external services (maps, Stripe, notifications).

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+ (3.11+ should work)

## Run the API

**You must run uvicorn from the `services/` folder** (your shell prompt should show `services`, not `front-end`). The Python package is named `app` and only exists there.

| Wrong | Result |
|--------|--------|
| Run `uvicorn app.main:app` from `front-end/` | `ModuleNotFoundError: No module named 'app'`, reloader watches `front-end/` |

From the **repository root**:

```bash
cd services
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Safer:** from repo root run **`./services/run-dev.sh`** (after `chmod +x services/run-dev.sh`). It `cd`s into `services/` for you, so it works even if you were in `front-end/` before.

Equivalent helper (enables **debug-level uvicorn logging** for 500 tracebacks): `./services/run-dev.sh` from the repo after `chmod +x services/run-dev.sh`.

**Confirm the API is running** (should return JSON, not “connection refused”):

```bash
curl -s http://127.0.0.1:8000/health
```

On first start, SQLite is created at `services/data/booma.db` and loaded from `references/data/synthetic-data.json`. Every seeded user’s password is **`demo`**. Optional `.env` in `services/` uses the `BOOMA_` prefix (for example `BOOMA_PROTOTYPE_PASSWORD`, `BOOMA_JWT_SECRET`, `BOOMA_LOG_LEVEL`); see `services/app/config.py` and `services/README.md` for logging.

## Run the front-end

From the **repository root**:

```bash
cd front-end
npm install
npm start
```

Open the URL Vite prints (default **http://localhost:9000**). API calls go to `/api` and `/health`, which are **proxied** to port 8000.

Example sign-in: **`sophie.zhang@gmail.com`** / **`demo`**.

### If login fails or the tab feels heavy

- **Both processes must be running:** API on **8000** and UI via **`npm start`** (not opening `index.html` as a file). The UI calls **`/api/...`** on the same origin; Vite **proxies** those to FastAPI.
- **`npm run build` alone** (or any static host without a proxy) will not forward `/api` unless you configure the same proxy or point the app at the full API URL.
- **`npm run preview`** uses the same proxy as dev (port **9000**); start the API first.
- **CORS:** the API only allows origins listed in `BOOMA_CORS_ORIGINS` (default `http://localhost:9000` and `http://127.0.0.1:9000`). If you change the Vite port, add it in `services/.env`.
- **Memory:** production builds use a lighter Aurelia mode (`useDev: false` when `mode === 'production'`). Prefer `npm run build` + `npm run preview` over leaving dev mode open for long sessions if RAM is tight.

## Documentation

- **Roadmap:** [ROADMAP.md](./ROADMAP.md)
- **Test plan:** [TEST_PLAN.md](./TEST_PLAN.md)
- **Product / architecture references:** `references/`

## Stubbed behaviour

- **Maps:** `GET /api/v1/stub/maps/autocomplete` returns landmarks from synthetic data only.
- **Payments:** `POST /api/v1/stub/payments/setup-intent` returns fake Stripe-like ids and logs only.
- **Notifications:** ride creation logs a stub message; no SMS/email is sent.

## Reset database

```bash
rm -f services/data/booma.db
```

Restart `uvicorn` to recreate and re-seed.

## Automated tests

Run this **from the repository root** as one line so the shell moves `services/` → `front-end/` correctly (`front-end` is not inside `services/`):

```bash
cd services && source .venv/bin/activate && pip install -r requirements.txt && pytest && cd ../front-end && npm test -- --run && npm run build
```

If you prefer two steps, run the second block **from the repository root** (open a new terminal or `cd ..` out of `services/` first):

```bash
cd front-end && npm test -- --run && npm run build
```

Latest counts and dates are recorded in [ROADMAP.md](./ROADMAP.md) under **Verification log**.
