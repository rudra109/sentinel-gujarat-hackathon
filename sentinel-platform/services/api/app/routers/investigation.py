"""
Investigation & Cross-Camera Timeline Router (B8 + B9)
- Plate search with filters
- Full cross-camera timeline for a plate
- GIS path for vehicle journey
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.detection import VehicleObservation
from app.models.camera import Camera
from app.models.user import User
from app.schemas.detection import ObservationOut, VehicleTimeline, TimelineEntry
from app.auth.security import get_current_user, REQUIRE_INVESTIGATOR_UP
from app.utils.audit import audit_log

router = APIRouter(prefix="/investigation", tags=["Investigation"])


@router.get("/search", response_model=List[ObservationOut])
async def search_observations(
    plate: Optional[str] = Query(None),
    camera_id: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    min_confidence: Optional[float] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await audit_log(
        db, "VEHICLE_SEARCH", user_id=current_user.id,
        metadata={"plate": plate, "camera_id": camera_id},
    )
    q = select(VehicleObservation)
    if plate:
        normalised = plate.upper().replace(" ", "").replace("-", "")
        q = q.where(VehicleObservation.plate_normalised == normalised)
    if camera_id:
        q = q.where(VehicleObservation.camera_id == camera_id)
    if start:
        q = q.where(VehicleObservation.observed_at >= start)
    if end:
        q = q.where(VehicleObservation.observed_at <= end)
    if min_confidence:
        q = q.where(VehicleObservation.plate_confidence >= min_confidence)
    q = q.order_by(VehicleObservation.observed_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return [ObservationOut.model_validate(o) for o in result.scalars().all()]


@router.get("/timeline/{plate}", response_model=VehicleTimeline)
async def get_vehicle_timeline(
    plate: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cross-camera ordered timeline for a specific plate (B9)."""
    normalised = plate.upper().replace(" ", "").replace("-", "")
    await audit_log(
        db, "TIMELINE_VIEW", user_id=current_user.id,
        entity_type="plate", entity_id=normalised,
    )

    # Get all observations ordered by time
    result = await db.execute(
        select(VehicleObservation)
        .where(VehicleObservation.plate_normalised == normalised)
        .order_by(VehicleObservation.observed_at)
    )
    observations = result.scalars().all()

    if not observations:
        return VehicleTimeline(
            plate=normalised, total_observations=0, first_seen=None,
            last_seen=None, cameras_count=0, timeline=[]
        )

    # Group by camera_id keeping chronological order
    camera_groups: dict[str, dict] = {}
    for obs in observations:
        cid = obs.camera_id
        if cid not in camera_groups:
            # Fetch camera metadata
            cam_result = await db.execute(
                select(Camera).where(Camera.external_camera_id == cid)
            )
            cam = cam_result.scalar_one_or_none()
            camera_groups[cid] = {
                "camera_id": cid,
                "camera_name": cam.name if cam else cid,
                "latitude": cam.latitude if cam else obs.latitude,
                "longitude": cam.longitude if cam else obs.longitude,
                "first_seen": obs.observed_at,
                "last_seen": obs.observed_at,
                "plate_normalised": obs.plate_normalised,
                "plate_confidence": obs.plate_confidence,
                "snapshot_path": obs.snapshot_path,
            }
        else:
            camera_groups[cid]["last_seen"] = obs.observed_at
            if obs.plate_confidence and (
                not camera_groups[cid]["plate_confidence"] or
                obs.plate_confidence > camera_groups[cid]["plate_confidence"]
            ):
                camera_groups[cid]["plate_confidence"] = obs.plate_confidence
                camera_groups[cid]["snapshot_path"] = obs.snapshot_path

    timeline_entries = [TimelineEntry(**g) for g in camera_groups.values()]
    # Re-sort by first_seen
    timeline_entries.sort(key=lambda x: x.first_seen)

    return VehicleTimeline(
        plate=normalised,
        total_observations=len(observations),
        first_seen=observations[0].observed_at,
        last_seen=observations[-1].observed_at,
        cameras_count=len(camera_groups),
        timeline=timeline_entries,
    )


@router.get("/gis-path/{plate}")
async def get_gis_path(plate: str, db: AsyncSession = Depends(get_db),
                        _: User = Depends(get_current_user)):
    """Returns GeoJSON LineString for vehicle journey map (B9 + B4)."""
    normalised = plate.upper().replace(" ", "").replace("-", "")
    result = await db.execute(
        select(VehicleObservation)
        .where(
            VehicleObservation.plate_normalised == normalised,
            VehicleObservation.latitude.isnot(None),
            VehicleObservation.longitude.isnot(None),
        )
        .order_by(VehicleObservation.observed_at)
    )
    observations = result.scalars().all()

    coordinates = [[o.longitude, o.latitude] for o in observations]
    return {
        "plate": normalised,
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": coordinates,
        },
        "properties": {
            "total_points": len(coordinates),
        },
    }
