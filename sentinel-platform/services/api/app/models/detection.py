from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from app.core.database import Base


class VehicleObservation(Base):
    __tablename__ = "vehicle_observations"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(100), nullable=False, index=True)
    track_id = Column(Integer, nullable=True)
    vehicle_type = Column(String(50), nullable=True)

    plate_raw = Column(String(20), nullable=True)
    plate_normalised = Column(String(20), nullable=True, index=True)
    plate_confidence = Column(Float, nullable=True)
    vehicle_detection_confidence = Column(Float, nullable=True)

    first_seen_pts = Column(Integer, nullable=True)
    last_seen_pts = Column(Integer, nullable=True)
    observed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    snapshot_path = Column(Text, nullable=True)
    plate_crop_path = Column(Text, nullable=True)

    reid_embedding_ref = Column(Text, nullable=True)

    # Dedup key: camera_id + track_id + plate_normalised + window
    dedup_key = Column(String(200), nullable=True, index=True)


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(20), nullable=False, index=True)
    category = Column(String(50), nullable=False, default="investigation")
    # stolen | suspect | investigation | blacklisted | test-target
    priority = Column(Integer, default=2)
    # 1=critical, 2=high, 3=medium, 4=low
    reason = Column(Text, nullable=True)
    active = Column(Integer, default=1)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    observation_id = Column(Integer, ForeignKey("vehicle_observations.id"), nullable=False)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), nullable=True)

    severity = Column(String(20), default="HIGH")
    match_type = Column(String(20), default="EXACT")
    # EXACT | POSSIBLE
    status = Column(String(20), default="OPEN")
    # OPEN | ACKNOWLEDGED | CLOSED

    plate_matched = Column(String(20), nullable=True)
    camera_id = Column(String(100), nullable=True)
    observed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    observation_id = Column(Integer, ForeignKey("vehicle_observations.id"), nullable=False)
    evidence_type = Column(String(20), nullable=False)
    # snapshot | plate_crop | clip
    file_path = Column(Text, nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(50), nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON string (renamed from 'metadata' — reserved by SQLAlchemy)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
