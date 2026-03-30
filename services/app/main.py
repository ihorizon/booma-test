import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.logging_setup import configure_logging
from app.middleware import RequestLoggingMiddleware
from app.routers import api_router
from app.seed import seed_if_empty

configure_logging()
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info("SQLite database: %s", settings.sqlite_path)
    log.info("Synthetic seed file: %s", settings.synthetic_data_path)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    except Exception:
        log.exception("Seed failed")
        raise
    finally:
        db.close()
    yield
    log.info("Application shutdown")


app = FastAPI(title="Booma Prototype API", lifespan=lifespan)
_cors = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if not _cors:
    _cors = ["http://localhost:9000", "http://127.0.0.1:9000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok", "storage": "sqlite"}
