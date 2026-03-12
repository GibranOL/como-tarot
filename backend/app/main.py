import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.db.database import create_db_and_tables
from app.rate_limiter import limiter
from app.api.auth import router as auth_router
from app.api.tarot import router as tarot_router
from app.api.horoscope import router as horoscope_router
from app.api.numerology import router as numerology_router
from app.api.compatibility import router as compatibility_router
from app.api.webhooks import router as webhooks_router

# Import models so SQLModel registers them before create_all
import app.models  # noqa: F401

logger = logging.getLogger("cosmotarot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: attempt DB table creation (Alembic is authoritative for prod).
    DB failure is non-fatal — the health check always works.
    """
    try:
        create_db_and_tables()
        logger.info("Database connection established and tables ready.")
    except Exception as exc:
        logger.warning(
            "Database not reachable at startup (set DATABASE_URL in .env): %s", exc
        )
    yield


# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CosmoTarot API",
    description="AI-powered tarot, astrology, and numerology backend",
    version="1.0.0",
    lifespan=lifespan,
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — tighten origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.APP_ENV == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(tarot_router)
app.include_router(horoscope_router)
app.include_router(numerology_router)
app.include_router(compatibility_router)
app.include_router(webhooks_router)


# ─── Health ───────────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
def health_check():
    """Verify the API is running and return basic status."""
    return {
        "status": "ok",
        "service": "CosmoTarot API",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.APP_ENV,
    }
