from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Enum as SAEnum
from geoalchemy2 import Geometry
from app.core.database import Base

import enum


class CameraStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    degraded = "degraded"
    reconnecting = "reconnecting"
    unknown = "unknown"


class AIStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    error = "error"


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    external_camera_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    location_text = Column(String(500), nullable=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location = Column(Geometry("POINT", srid=4326), nullable=True)

    codec = Column(String(20), nullable=True)
    resolution = Column(String(20), nullable=True)
    bitrate = Column(Integer, nullable=True)

    rtsp_url = Column(Text, nullable=True)
    hls_url = Column(Text, nullable=True)
    webrtc_url = Column(Text, nullable=True)

    live_status = Column(SAEnum(CameraStatus), default=CameraStatus.unknown, nullable=False)
    ai_status = Column(SAEnum(AIStatus), default=AIStatus.inactive, nullable=False)
    ai_enabled = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class CameraHealth(Base):
    __tablename__ = "camera_health"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(100), nullable=False, index=True)
    online = Column(Boolean, default=False)
    last_frame_pts = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    codec = Column(String(20), nullable=True)
    resolution = Column(String(20), nullable=True)
    blur_score = Column(Float, nullable=True)
    brightness_score = Column(Float, nullable=True)
    freeze_status = Column(Boolean, default=False)
    is_dark = Column(Boolean, default=False)
    is_overexposed = Column(Boolean, default=False)
    decode_error_rate = Column(Float, nullable=True)
    ai_worker_status = Column(String(20), nullable=True)
    last_checked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
