"""
Person A — Standard AI Event Publisher (Module A8)
Publishes standardized JSON ANPR detection events and health status events to Redis Streams.
"""
import json
import uuid
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import redis.asyncio as aioredis

from config import settings

logger = logging.getLogger("redis-publisher")


class RedisEventPublisher:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client = None

    async def connect(self):
        if self.redis_client is None:
            self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
            logger.info(f"Connected to Redis Stream at: {self.redis_url}")

    async def publish_anpr_event(
        self,
        camera_id: str,
        vehicle_type: str,
        vehicle_confidence: float,
        track_id: int,
        raw_plate: str,
        normalised_plate: str,
        plate_confidence: float,
        snapshot_url: str,
        plate_crop_url: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        pts_ms: Optional[int] = None
    ) -> str:
        """
        Publishes ANPR detection event matching Person B contract on stream: sentinel:ai:events
        """
        await self.connect()
        if pts_ms is None:
            pts_ms = int(time.time() * 1000)

        event_payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": "ANPR_DETECTION",
            "camera_id": camera_id,
            "pts_ms": pts_ms,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "location": {
                "lat": lat if lat is not None else 23.0225,
                "lon": lon if lon is not None else 72.5714
            },
            "vehicle": {
                "type": vehicle_type,
                "confidence": round(vehicle_confidence, 2),
                "track_id": track_id
            },
            "plate": {
                "raw": raw_plate,
                "normalised": normalised_plate,
                "confidence": round(plate_confidence, 2)
            },
            "evidence": {
                "snapshot": snapshot_url,
                "plate_crop": plate_crop_url
            }
        }

        try:
            # Publish payload to Redis Stream
            msg_id = await self.redis_client.xadd(
                settings.AI_EVENT_STREAM_KEY,
                {"data": json.dumps(event_payload)}
            )
            logger.info(f"Published ANPR event [{msg_id}]: cam={camera_id} plate={normalised_plate} track={track_id}")
            return msg_id
        except Exception as e:
            logger.error(f"Failed to publish Redis ANPR event: {e}")
            return ""

    async def publish_health_event(
        self,
        camera_id: str,
        online: bool = True,
        blur_score: float = 85.0,
        brightness_score: float = 120.0,
        freeze_status: bool = False,
        is_dark: bool = False,
        latency_ms: float = 45.0
    ) -> str:
        """
        Publishes camera health event on stream: sentinel:health:events
        """
        await self.connect()
        payload = {
            "camera_id": camera_id,
            "online": online,
            "ai_worker": "healthy",
            "last_pts_ms": int(time.time() * 1000),
            "blur_score": blur_score,
            "brightness_score": brightness_score,
            "freeze_status": freeze_status,
            "is_dark": is_dark,
            "latency_ms": latency_ms
        }

        try:
            msg_id = await self.redis_client.xadd(
                settings.HEALTH_EVENT_STREAM_KEY,
                {"data": json.dumps(payload)}
            )
            return msg_id
        except Exception as e:
            logger.error(f"Failed to publish camera health event: {e}")
            return ""

    async def close(self):
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
