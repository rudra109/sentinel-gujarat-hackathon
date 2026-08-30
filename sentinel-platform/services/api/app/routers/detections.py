"""
Detections Router
- REST endpoint for Person A to POST AI detection events
- Query detections
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.detection import VehicleObservation
from app.models.user import User
from app.schemas.detection import ANPRDetectionEvent, ObservationOut
from app.auth.security import get_current_user
from app.services.event_processor import process_anpr_event

router = APIRouter(prefix="/detections", tags=["Detections"])


@router.post("/ingest")
async def ingest_detection(event: ANPRDetectionEvent, db: AsyncSession = Depends(get_db)):
    """
    REST fallback for Person A to POST AI detection events directly.
    Primary path is the Redis stream consumer in event-worker.
    """
    await process_anpr_event(event, db)
    return {"ok": True}


@router.get("", response_model=List[ObservationOut])
async def list_detections(
    camera_id: Optional[str] = Query(None),
    plate: Optional[str] = Query(None),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(VehicleObservation)
    if camera_id:
        q = q.where(VehicleObservation.camera_id == camera_id)
    if plate:
        normalised = plate.upper().replace(" ", "").replace("-", "")
        q = q.where(VehicleObservation.plate_normalised == normalised)
    if start:
        q = q.where(VehicleObservation.observed_at >= start)
    if end:
        q = q.where(VehicleObservation.observed_at <= end)
    q = q.order_by(VehicleObservation.observed_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return [ObservationOut.model_validate(o) for o in result.scalars().all()]
