"""
Person A — AI / Video / Stream Engine Configuration
"""
import os
from pydantic_settings import BaseSettings


class PipelineSettings(BaseSettings):
    # Redis Stream configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    AI_EVENT_STREAM_KEY: str = os.getenv("AI_EVENT_STREAM_KEY", "sentinel:ai:events")
    HEALTH_EVENT_STREAM_KEY: str = os.getenv("HEALTH_EVENT_STREAM_KEY", "sentinel:health:events")

    # FastAPI Backend URL for camera sync
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    CAMERA_SYNC_INTERVAL: int = 30  # seconds

    # AI Pipeline Settings
    VEHICLE_CONF_THRESHOLD: float = 0.40
    PLATE_CONF_THRESHOLD: float = 0.35
    OCR_CONF_THRESHOLD: float = 0.50

    # Sampling & Deduplication
    FRAME_SAMPLE_RATE: int = 5  # Process every 5th frame
    DEDUP_WINDOW_SECONDS: int = 30  # Same track + plate within 30s = single observation

    # Model Weights (Ultralytics / OpenCV / Local)
    VEHICLE_MODEL_PATH: str = os.getenv("VEHICLE_MODEL_PATH", "yolov8n.pt")
    PLATE_MODEL_PATH: str = os.getenv("PLATE_MODEL_PATH", "plate_detector.pt")

    # Evidence Directory
    EVIDENCE_DIR: str = os.path.join(os.path.dirname(__file__), "..", "api", "static", "evidence")

    class Config:
        env_file = ".env"
        extra = "allow"


settings = PipelineSettings()
