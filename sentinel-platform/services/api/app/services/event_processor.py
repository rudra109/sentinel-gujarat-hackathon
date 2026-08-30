"""
Core ANPR Event Processing Logic (shared by REST ingest and Redis event-worker)
Handles:
- Deduplication
- Watchlist matching (exact + near-match)
- Alert creation
- WebSocket broadcast
"""
import json
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

from Levenshtein import distance as levenshtein_distance
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.detection import VehicleObservation, Watchlist, Alert
from app.schemas.detection import ANPRDetectionEvent
from app.utils.ws_manager import manager


def normalise_plate(raw: str) -> str:
    """Uppercase, strip spaces/dashes."""
    return raw.upper().replace(" ", "").replace("-", "") if raw else ""


def make_dedup_key(camera_id: str, track_id: Optional[int], plate_normalised: str) -> str:
    return f"{camera_id}:{track_id}:{plate_normalised}"


async def process_anpr_event(event: ANPRDetectionEvent, db: AsyncSession):
    """
    Full pipeline:
    1. Normalise plate
    2. Dedup check (same camera+track+plate within DEDUP_WINDOW_SECONDS)
    3. Store/update vehicle_observation
    4. Run watchlist match
    5. Create alert if match
    6. Broadcast via WebSocket
    """
    plate_normalised = ""
    if event.plate and event.plate.raw:
        plate_normalised = normalise_plate(event.plate.raw)
    if event.plate and event.plate.normalised:
        plate_normalised = normalise_plate(event.plate.normalised)

    track_id = event.vehicle.track_id if event.vehicle else None
    dedup_key = make_dedup_key(event.camera_id, track_id, plate_normalised)

    # ── Deduplication ──────────────────────────────────────────
    window_start = datetime.now(timezone.utc) - timedelta(seconds=settings.DEDUP_WINDOW_SECONDS)
    existing_result = await db.execute(
        select(VehicleObservation).where(
            VehicleObservation.dedup_key == dedup_key,
            VehicleObservation.observed_at >= window_start,
        )
    )
    existing = existing_result.scalars().first()

    if existing:
        # Update last_seen and best confidence
        existing.last_seen_pts = event.pts_ms
        if event.plate and event.plate.confidence:
            if not existing.plate_confidence or event.plate.confidence > existing.plate_confidence:
                existing.plate_confidence = event.plate.confidence
                if event.evidence and event.evidence.plate_crop:
                    existing.plate_crop_path = event.evidence.plate_crop
        await db.commit()
        return  # No new alert for duplicate

    # ── Create new observation ─────────────────────────────────
    obs_time = datetime.now(timezone.utc)
    if event.observed_at:
        try:
            obs_time = datetime.fromisoformat(event.observed_at.replace("Z", "+00:00"))
        except Exception:
            pass

    observation = VehicleObservation(
        camera_id=event.camera_id,
        track_id=track_id,
        vehicle_type=event.vehicle.type if event.vehicle else None,
        plate_raw=event.plate.raw if event.plate else None,
        plate_normalised=plate_normalised,
        plate_confidence=event.plate.confidence if event.plate else None,
        vehicle_detection_confidence=event.vehicle.confidence if event.vehicle else None,
        first_seen_pts=event.pts_ms,
        last_seen_pts=event.pts_ms,
        observed_at=obs_time,
        latitude=event.location.lat if event.location else None,
        longitude=event.location.lon if event.location else None,
        snapshot_path=event.evidence.snapshot if event.evidence else None,
        plate_crop_path=event.evidence.plate_crop if event.evidence else None,
        dedup_key=dedup_key,
    )
    db.add(observation)
    await db.flush()  # Get observation.id

    # ── Watchlist Match ────────────────────────────────────────
    if plate_normalised:
        wl_result = await db.execute(
            select(Watchlist).where(Watchlist.active == 1)
        )
        watchlists = wl_result.scalars().all()

        for wl in watchlists:
            # Skip expired
            if wl.expires_at and wl.expires_at < datetime.now(timezone.utc):
                continue

            wl_plate = normalise_plate(wl.plate_number)
            edit_dist = levenshtein_distance(plate_normalised, wl_plate)

            match_type = None
            severity = "HIGH"

            if edit_dist == 0:
                match_type = "EXACT"
                severity = "CRITICAL" if wl.priority == 1 else "HIGH"
            elif edit_dist == 1:
                match_type = "POSSIBLE"
                severity = "MEDIUM"

            if match_type:
                alert = Alert(
                    observation_id=observation.id,
                    watchlist_id=wl.id,
                    severity=severity,
                    match_type=match_type,
                    status="OPEN",
                    plate_matched=plate_normalised,
                    camera_id=event.camera_id,
                    observed_at=obs_time,
                )
                db.add(alert)
                await db.flush()

                # ── WebSocket broadcast ────────────────────────
                await manager.broadcast({
                    "type": "ALERT",
                    "alert_id": alert.id,
                    "match_type": match_type,
                    "severity": severity,
                    "plate": plate_normalised,
                    "watchlist_plate": wl.plate_number,
                    "camera_id": event.camera_id,
                    "observed_at": obs_time.isoformat(),
                    "snapshot": event.evidence.snapshot if event.evidence else None,
                    "plate_crop": event.evidence.plate_crop if event.evidence else None,
                })

    await db.commit()
