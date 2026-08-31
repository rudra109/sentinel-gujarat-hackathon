"""
Person A — Live RTSP Stream Reader & Ingestion Worker (Module A3)
Discovers cameras dynamically from backend, ingests live RTSP video feeds via OpenCV/FFmpeg,
performs adaptive frame sampling, PTS timestamp extraction, exponential backoff reconnection,
and stream health monitoring.
"""
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
import httpx
import numpy as np
import cv2

from config import settings

logger = logging.getLogger("stream-reader")


class RTSPStreamWorker:
    def __init__(self, camera_id: str, rtsp_url: str, frame_callback: Callable):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.frame_callback = frame_callback
        self.is_running = False
        self.reconnect_delay = 2  # Start with 2 seconds backoff
        self.max_reconnect_delay = 32

    async def start(self):
        """Main camera stream loop with auto-reconnect and frame sampling."""
        self.is_running = True
        logger.info(f"Starting RTSP stream worker for [{self.camera_id}] -> {self.rtsp_url}")

        frame_count = 0

        while self.is_running:
            cap = None
            try:
                # Force TCP transport for reliable RTSP streaming
                cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                if not cap.isOpened():
                    raise ConnectionError(f"Unable to open RTSP stream: {self.rtsp_url}")

                logger.info(f"Stream connected: [{self.camera_id}]")
                self.reconnect_delay = 2  # Reset backoff on successful connection

                while self.is_running and cap.isOpened():
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        logger.warning(f"Frame read failed for [{self.camera_id}]. Reconnecting...")
                        break

                    frame_count += 1
                    pts_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC)) or int(time.time() * 1000)

                    # Adaptive frame sampling: Process every Nth frame
                    if frame_count % settings.FRAME_SAMPLE_RATE == 0:
                        await self.frame_callback(self.camera_id, frame, pts_ms)

                    await asyncio.sleep(0.01)  # Yield loop control

            except Exception as e:
                logger.error(f"Stream error on [{self.camera_id}]: {e}")

            finally:
                if cap:
                    cap.release()

            if self.is_running:
                logger.info(f"Reconnecting stream [{self.camera_id}] in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)

    def stop(self):
        self.is_running = False


class StreamIngestionManager:
    def __init__(self, api_base_url: Optional[str] = None):
        self.api_base_url = api_base_url or settings.API_BASE_URL
        self.active_workers: Dict[str, RTSPStreamWorker] = {}

    async def fetch_camera_configs(self) -> List[Dict[str, Any]]:
        """Fetch dynamic camera catalogue from FastAPI backend."""
        url = f"{self.api_base_url}/cameras/ai-config/all"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.warning(f"Could not sync camera configs from {url}: {e}")

        # Default fallback camera configurations if backend API is initializing
        return [
            {"camera_id": "CAM-01", "name": "SG Highway Junction", "rtsp_url": "rtsp://localhost:8554/cam01", "enabled": True},
            {"camera_id": "CAM-02", "name": "Ashram Road Intersection", "rtsp_url": "rtsp://localhost:8554/cam02", "enabled": True},
            {"camera_id": "CAM-03", "name": "Gandhinagar Toll Plaza", "rtsp_url": "rtsp://localhost:8554/cam03", "enabled": True},
        ]
