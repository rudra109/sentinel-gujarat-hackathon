from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://sentinel:sentinel_secret@localhost:5432/sentinel_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "sentinel-evidence"
    MINIO_PUBLIC_URL: str = "http://localhost:9000"

    # JWT
    SECRET_KEY: str = "CHANGE_ME"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Sentinel Sandbox
    SENTINEL_INGEST_URL: str = "https://sentinel.gujarat.gov.in/api/ingest"
    SENTINEL_API_KEY: str = ""
    CAMERA_SYNC_INTERVAL_SECONDS: int = 60

    # AI Event Stream Keys
    AI_EVENT_STREAM_KEY: str = "sentinel:ai:events"
    HEALTH_EVENT_STREAM_KEY: str = "sentinel:health:events"

    # Deduplication
    DEDUP_WINDOW_SECONDS: int = 30

    # CORS — accepts either JSON array or comma-separated string
    CORS_ORIGINS: Union[List[str], str] = "http://localhost:5173,http://localhost:3000"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Handle JSON array format ["...","..."] or comma-separated
            v = v.strip()
            if v.startswith("["):
                import json
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
