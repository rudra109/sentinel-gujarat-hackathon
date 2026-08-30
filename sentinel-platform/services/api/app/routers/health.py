"""
Camera Health Dashboard Router (B10)
- Receive health events from Person A via REST (also consumed by event-worker from Redis)
- Query health status per camera
"""
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.camera import CameraHealth, Camera, CameraStatus
from app.models.user import User
from app.schemas.camera import CameraHealthOut
from app.schemas.detection import HealthEvent
from app.auth.security import get_current_user

router = APIRouter(prefix="/health", tags=["Camera Health"])


@router.get("", response_model=List[CameraHealthOut])
async def list_health(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(CameraHealth).order_by(CameraHealth.last_checked_at.desc()))
    return [CameraHealthOut.model_validate(h) for h in result.scalars().all()]


@router.get("/{camera_id}", response_model=CameraHealthOut)
async def get_camera_health(camera_id: str, db: AsyncSession = Depends(get_db),
                             _: User = Depends(get_current_user)):
    result = await db.execute(
        select(CameraHealth).where(CameraHealth.camera_id == camera_id)
        .order_by(CameraHealth.last_checked_at.desc())
    )
    health = result.scalars().first()
    if not health:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Health record not found")
    return CameraHealthOut.model_validate(health)


@router.post("/ingest")
async def ingest_health_event(event: HealthEvent, db: AsyncSession = Depends(get_db)):
    """
    REST endpoint for Person A to POST health events.
    (Also consumed via Redis stream in the event-worker.)
    """
    from datetime import datetime, timezone
    from sqlalchemy import update

    # Upsert health record
    result = await db.execute(
        select(CameraHealth).where(CameraHealth.camera_id == event.camera_id)
        .order_by(CameraHealth.last_checked_at.desc())
    )
    health = result.scalars().first()
    if health is None:
        health = CameraHealth(camera_id=event.camera_id)
        db.add(health)

    health.online = event.online
    health.last_frame_pts = event.last_pts_ms
    health.ai_worker_status = event.ai_worker
    health.blur_score = event.blur_score
    health.brightness_score = event.brightness_score
    health.freeze_status = event.freeze_status or False
    health.is_dark = event.is_dark or False
    health.latency_ms = event.latency_ms
    health.last_checked_at = datetime.now(timezone.utc)

    # Update camera live_status
    status = CameraStatus.online if event.online else CameraStatus.offline
    cam_result = await db.execute(
        select(Camera).where(Camera.external_camera_id == event.camera_id)
    )
    cam = cam_result.scalar_one_or_none()
    if cam:
        cam.live_status = status

    await db.commit()
    return {"ok": True}
