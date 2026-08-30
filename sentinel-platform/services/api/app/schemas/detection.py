from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# ─── AI Event Contract (received from Person A) ──────────────────────────────

class VehicleInfo(BaseModel):
    type: Optional[str] = None
    confidence: Optional[float] = None
    track_id: Optional[int] = None


class PlateInfo(BaseModel):
    raw: Optional[str] = None
    normalised: Optional[str] = None
    confidence: Optional[float] = None


class EvidenceInfo(BaseModel):
    snapshot: Optional[str] = None
    plate_crop: Optional[str] = None


class LocationInfo(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None


class ANPRDetectionEvent(BaseModel):
    """Standard AI event contract from Person A."""
    event_id: Optional[str] = None
    event_type: str = "ANPR_DETECTION"
    camera_id: str
    pts_ms: Optional[int] = None
    observed_at: Optional[str] = None
    location: Optional[LocationInfo] = None
    vehicle: Optional[VehicleInfo] = None
    plate: Optional[PlateInfo] = None
    evidence: Optional[EvidenceInfo] = None


class HealthEvent(BaseModel):
    """Camera health event from Person A."""
    camera_id: str
    online: bool
    ai_worker: Optional[str] = None
    last_pts_ms: Optional[int] = None
    blur_score: Optional[float] = None
    brightness_score: Optional[float] = None
    freeze_status: Optional[bool] = None
    is_dark: Optional[bool] = None
    latency_ms: Optional[float] = None


# ─── Vehicle Observation Schemas ──────────────────────────────────────────────

class ObservationOut(BaseModel):
    id: int
    camera_id: str
    track_id: Optional[int]
    vehicle_type: Optional[str]
    plate_raw: Optional[str]
    plate_normalised: Optional[str]
    plate_confidence: Optional[float]
    vehicle_detection_confidence: Optional[float]
    observed_at: datetime
    latitude: Optional[float]
    longitude: Optional[float]
    snapshot_path: Optional[str]
    plate_crop_path: Optional[str]

    class Config:
        from_attributes = True


# ─── Watchlist Schemas ────────────────────────────────────────────────────────

class WatchlistCreate(BaseModel):
    plate_number: str
    category: str = "investigation"
    priority: int = 2
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None


class WatchlistOut(BaseModel):
    id: int
    plate_number: str
    category: str
    priority: int
    reason: Optional[str]
    active: int
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Alert Schemas ────────────────────────────────────────────────────────────

class AlertOut(BaseModel):
    id: int
    observation_id: int
    watchlist_id: Optional[int]
    severity: str
    match_type: str
    status: str
    plate_matched: Optional[str]
    camera_id: Optional[str]
    observed_at: Optional[datetime]
    created_at: datetime
    acknowledged_by: Optional[int]
    acknowledged_at: Optional[datetime]
    notes: Optional[str]

    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    notes: Optional[str] = None


# ─── Investigation Schemas ────────────────────────────────────────────────────

class TimelineEntry(BaseModel):
    camera_id: str
    camera_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    first_seen: datetime
    last_seen: datetime
    plate_normalised: Optional[str]
    plate_confidence: Optional[float]
    snapshot_path: Optional[str]


class VehicleTimeline(BaseModel):
    plate: str
    total_observations: int
    first_seen: Optional[datetime]
    last_seen: Optional[datetime]
    cameras_count: int
    timeline: List[TimelineEntry]


# ─── Audit Log Schemas ────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    metadata: Optional[str]
    ip_address: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True
