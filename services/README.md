# Booma prototype API

FastAPI application with SQLite storage and stubbed integrations for local development.

**Import rule:** run uvicorn **only** with current directory = `services/` (where the `app/` package lives). Running from `front-end/` causes `ModuleNotFoundError: No module named 'app'`. Use `./run-dev.sh` from this folder, or `../services/run-dev.sh` from the repo root.

## Run

**One-liner (from `services/` after venv + pip install):**

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Or use the helper script (enables **uvicorn `--log-level debug`** so tracebacks for 500s are verbose):

```bash
chmod +x run-dev.sh   # once
./run-dev.sh
```

**Check that it is actually up:**

```bash
curl -s http://127.0.0.1:8000/health
# expect: {"status":"ok","storage":"sqlite"}
```

If `curl` fails with “connection refused”, the API is not running — the front-end proxy will then fail or return errors.

### Logging

- Every request is logged as `METHOD path -> status (N ms)` under the logger `booma.request`.
- Startup logs the resolved **SQLite path** and **synthetic data path** (seed file).
- Set **`BOOMA_LOG_LEVEL=DEBUG`** in `.env` (or the environment) for more application log detail.
- Uvicorn’s **`--log-level debug`** (as in `run-dev.sh`) prints full Python tracebacks when an endpoint raises an unhandled exception (typical cause of HTTP 500).

## Configuration

Optional `.env` in this directory (see `app/config.py`):

| Variable | Purpose |
|----------|---------|
| `BOOMA_JWT_SECRET` | HMAC secret for access tokens |
| `BOOMA_PROTOTYPE_PASSWORD` | Password hashed for all users at seed time (default `demo`) |
| `BOOMA_CORS_ORIGINS` | Comma-separated list, e.g. `http://localhost:9000,http://127.0.0.1:5173` if your Vite port differs |
| `BOOMA_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` (default `INFO`) |

## Layout

| Path | Role |
|------|------|
| `app/main.py` | FastAPI app, CORS, lifespan (create DB + seed) |
| `app/routers/` | HTTP routes under `/api/v1` |
| `app/stubs/` | In-memory maps / payment / notification stubs |
| `app/seed.py` | One-time import from `references/data/synthetic-data.json` |
| `data/booma.db` | SQLite file (gitignored) |

## Tests

```bash
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

See the repository [TEST_PLAN.md](../TEST_PLAN.md) and [ROADMAP.md](../ROADMAP.md) (verification log) for scope and last results.
