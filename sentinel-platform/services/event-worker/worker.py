"""
Sentinel Event Worker (B7)
Consumes AI events from Redis Streams published by Person A.
- ANPR_DETECTION events → DB → watchlist match → alert → WebSocket broadcast
- HEALTH events → DB camera health update
"""
import asyncio
import json
import logging
import sys
import os

# Add the API app to path so we can share models and services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.redis_client import get_redis
from app.schemas.detection import ANPRDetectionEvent, HealthEvent
from app.services.event_processor import process_anpr_event
from app.routers.health import ingest_health_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("event-worker")

CONSUMER_GROUP = "sentinel-platform"
CONSUMER_NAME = "worker-1"


async def ensure_streams(redis):
    """Create consumer groups if they don't exist."""
    for stream_key in [settings.AI_EVENT_STREAM_KEY, settings.HEALTH_EVENT_STREAM_KEY]:
        try:
            await redis.xgroup_create(stream_key, CONSUMER_GROUP, id="0", mkstream=True)
            logger.info(f"Created consumer group for stream: {stream_key}")
        except Exception as e:
            if "BUSYGROUP" in str(e):
                pass  # Already exists
            else:
                logger.warning(f"Stream group creation: {e}")


async def process_ai_stream(redis, db):
    """Read ANPR detection events from Redis Stream."""
    try:
        messages = await redis.xreadgroup(
            CONSUMER_GROUP,
            CONSUMER_NAME,
            {settings.AI_EVENT_STREAM_KEY: ">"},
            count=10,
            block=100,
        )
    except Exception as e:
        logger.error(f"Error reading AI stream: {e}")
        return

    if not messages:
        return

    for stream_name, entries in messages:
        for entry_id, fields in entries:
            try:
                raw = fields.get("data") or fields.get("event")
                if not raw:
                    raw = json.dumps(dict(fields))
                data = json.loads(raw) if isinstance(raw, str) else fields
                event = ANPRDetectionEvent(**data)
                await process_anpr_event(event, db)
                await redis.xack(settings.AI_EVENT_STREAM_KEY, CONSUMER_GROUP, entry_id)
                logger.info(f"Processed ANPR event: cam={event.camera_id} plate={event.plate.normalised if event.plate else 'N/A'}")
            except Exception as e:
                logger.error(f"Failed to process event {entry_id}: {e}")


async def process_health_stream(redis, db):
    """Read health events from Redis Stream."""
    try:
        messages = await redis.xreadgroup(
            CONSUMER_GROUP,
            CONSUMER_NAME,
            {settings.HEALTH_EVENT_STREAM_KEY: ">"},
            count=20,
            block=100,
        )
    except Exception as e:
        logger.error(f"Error reading health stream: {e}")
        return

    if not messages:
        return

    for stream_name, entries in messages:
        for entry_id, fields in entries:
            try:
                raw = fields.get("data") or json.dumps(dict(fields))
                data = json.loads(raw) if isinstance(raw, str) else fields
                event = HealthEvent(**data)
                # Reuse the health ingest logic
                from app.routers.health import _upsert_health
                await _upsert_health(event, db)
                await redis.xack(settings.HEALTH_EVENT_STREAM_KEY, CONSUMER_GROUP, entry_id)
            except Exception as e:
                logger.error(f"Failed to process health event {entry_id}: {e}")


async def expiry_watchlist_job(db):
    """Deactivate expired watchlist entries."""
    from datetime import datetime, timezone
    from sqlalchemy import update
    from app.models.detection import Watchlist
    from sqlalchemy import and_

    await db.execute(
        update(Watchlist)
        .where(
            and_(
                Watchlist.active == 1,
                Watchlist.expires_at < datetime.now(timezone.utc),
            )
        )
        .values(active=0)
    )
    await db.commit()


async def main():
    logger.info("Sentinel Event Worker starting...")

    # Init DB
    async with engine.begin() as conn:
        await conn.execute(__import__('sqlalchemy').text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(Base.metadata.create_all)

    redis = await get_redis()
    await ensure_streams(redis)

    loop_count = 0

    async with AsyncSessionLocal() as db:
        logger.info("Event Worker ready. Listening for events...")
        while True:
            try:
                await process_ai_stream(redis, db)
                await process_health_stream(redis, db)

                # Run expiry check every 5 minutes
                loop_count += 1
                if loop_count % 300 == 0:
                    await expiry_watchlist_job(db)

            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(2)

            await asyncio.sleep(0.1)  # Brief yield


if __name__ == "__main__":
    asyncio.run(main())
