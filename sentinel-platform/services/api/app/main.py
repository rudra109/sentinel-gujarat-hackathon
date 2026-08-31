"""
Sentinel FastAPI Application Entry Point (B1)
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.core.database import engine, Base
from app.core.redis_client import close_redis
from app.routers import auth, cameras, watchlist, alerts, detections, investigation, health, audit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def startup_camera_sync():
    """Periodic camera sync from Sentinel /api/ingest."""
    from app.core.database import AsyncSessionLocal
    from app.routers.cameras import _sync_from_ingest
    async with AsyncSessionLocal() as db:
        try:
            await _sync_from_ingest(db)
            logger.info("Periodic camera sync completed.")
        except Exception as e:
            logger.error(f"Camera sync failed: {e}")


async def auto_seed_admin():
    """
    Auto-create the default super_admin on first startup.
    No seed script needed — just start the API and the admin is ready.
    Credentials: admin@sentinel.gujarat.gov.in / Sentinel@2026
    """
    from app.core.database import AsyncSessionLocal
    from app.models.user import User
    from sqlalchemy import select
    import bcrypt as _bcrypt

    ADMIN_EMAIL = "admin@sentinel.gujarat.gov.in"
    ADMIN_PASSWORD = "Sentinel@2026"

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
            if result.scalar_one_or_none():
                logger.info("Admin user already exists — skipping auto-seed.")
                return
            # Use bcrypt directly — compatible with all versions including 4.x on Python 3.13
            pw_hash = _bcrypt.hashpw(ADMIN_PASSWORD.encode("utf-8"), _bcrypt.gensalt(12)).decode("utf-8")
            admin = User(
                email=ADMIN_EMAIL,
                full_name="Sentinel Administrator",
                password_hash=pw_hash,
                role="super_admin",
                is_active=True,
            )
            db.add(admin)
            await db.commit()
            logger.info("✅ Auto-seeded admin: admin@sentinel.gujarat.gov.in / Sentinel@2026")
        except Exception as e:
            logger.error(f"Auto-seed failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────
    logger.info("Starting Sentinel API...")

    # Create tables (dev convenience — use Alembic for production)
    async with engine.begin() as conn:
        # PostGIS extension
        await conn.execute(__import__('sqlalchemy').text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(Base.metadata.create_all)

    # Auto-create admin user if not present (no seed script needed)
    await auto_seed_admin()

    # Schedule periodic camera sync
    scheduler.add_job(
        startup_camera_sync,
        "interval",
        seconds=settings.CAMERA_SYNC_INTERVAL_SECONDS,
        id="camera_sync",
        replace_existing=True,
    )
    scheduler.start()

    # Initial sync on startup
    asyncio.create_task(startup_camera_sync())

    logger.info("Sentinel API ready.")
    yield

    # ── Shutdown ──────────────────────────────────────────────
    scheduler.shutdown()
    await close_redis()
    await engine.dispose()
    logger.info("Sentinel API shutdown complete.")


app = FastAPI(
    title="Sentinel Unified Intelligence Platform",
    description="Gujarat Police CCTV Intelligence Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(cameras.router)
app.include_router(watchlist.router)
app.include_router(alerts.router)
app.include_router(detections.router)
app.include_router(investigation.router)
app.include_router(health.router)
app.include_router(audit.router)


@app.get("/", tags=["System"])
async def root():
    return {
        "service": "Sentinel Unified Intelligence Platform",
        "version": "1.0.0",
        "status": "operational",
    }


@app.get("/ping", tags=["System"])
async def ping():
    return {"pong": True}
