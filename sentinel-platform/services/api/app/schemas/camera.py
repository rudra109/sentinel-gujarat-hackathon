from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class CameraBase(BaseModel):
    external_camera_id: str
    name: str
    department: Optional[str] = None
    district: Optional[str] = None
    location_text: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rtsp_url: Optional[str] = None
    hls_url: Optional[str] = None
    webrtc_url: Optional[str] = None
    codec: Optional[str] = None
    resolution: Optional[str] = None
    bitrate: Optional[int] = None


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    district: Optional[str] = None
    location_text: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rtsp_url: Optional[str] = None
    hls_url: Optional[str] = None
    webrtc_url: Optional[str] = None
    ai_enabled: Optional[bool] = None


class CameraOut(CameraBase):
    id: int
    live_status: str
    ai_status: str
    ai_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CameraHealthOut(BaseModel):
    camera_id: str
    online: bool
    last_frame_pts: Optional[int]
    latency_ms: Optional[float]
    codec: Optional[str]
    resolution: Optional[str]
    blur_score: Optional[float]
    brightness_score: Optional[float]
    freeze_status: bool
    is_dark: bool
    is_overexposed: bool
    decode_error_rate: Optional[float]
    ai_worker_status: Optional[str]
    last_checked_at: datetime

    class Config:
        from_attributes = True


class CameraConfigForAI(BaseModel):
    """Sent to Person A's stream worker."""
    camera_id: str
    rtsp_url: str
    enabled: bool
