"""
Person A — Main AI Stream Engine & Inference Pipeline Entry Point
Orchestrates multi-camera RTSP ingestion, vehicle detection, tracking, license plate detection,
ANPR OCR recognition, deduplication, evidence storage, and Redis stream publishing.
"""
import asyncio
import logging
import signal
import sys
import os
import time
import numpy as np

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config import settings
from ingest.stream_reader import StreamIngestionManager, RTSPStreamWorker
from models.vehicle_detector import VehicleDetector
from models.plate_detector import PlateDetector
from models.ocr_engine import PlateOCREngine
from tracking.tracker import CameraTracker
from evidence.storage import EvidenceStorage
from publisher.redis_publisher import RedisEventPublisher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ai-pipeline-main")


class SentinelAIEngine:
    def __init__(self):
        logger.info("Initializing Sentinel AI Stream Engine (Person A)...")
        self.vehicle_detector = VehicleDetector(
            model_path=settings.VEHICLE_MODEL_PATH,
            conf_thresh=settings.VEHICLE_CONF_THRESHOLD,
        )
        self.plate_detector = PlateDetector(
            model_path=settings.PLATE_MODEL_PATH,
            conf_thresh=settings.PLATE_CONF_THRESHOLD,
        )
        self.ocr_engine = PlateOCREngine(use_easyocr=True)
        self.storage = EvidenceStorage(storage_dir=settings.EVIDENCE_DIR)
        self.publisher = RedisEventPublisher(redis_url=settings.REDIS_URL)
        self.trackers: dict[str, CameraTracker] = {}
        self.is_running = False

    async def process_frame(self, camera_id: str, frame: np.ndarray, pts_ms: int):
        """Sequential Multi-Stage Pipeline: Frame -> Vehicle -> Track -> Plate -> OCR -> Deduplication -> Publish"""
        if camera_id not in self.trackers:
            self.trackers[camera_id] = CameraTracker(camera_id, dedup_window=settings.DEDUP_WINDOW_SECONDS)

        tracker = self.trackers[camera_id]

        # 1. Vehicle Detection
        detections = self.vehicle_detector.detect(frame)
        if not detections:
            return

        # 2. Within-Camera Tracking
        active_tracks = tracker.update_tracks(detections)

        # 3. License Plate Detection & OCR on tracked vehicle crops
        for track in active_tracks:
            res = self.plate_detector.detect_plate(track.bbox and frame[track.bbox[1]:track.bbox[3], track.bbox[0]:track.bbox[2]])
            if res:
                plate_box, plate_conf, plate_crop = res
                raw_text, norm_text, ocr_conf = self.ocr_engine.recognize(plate_crop)

                if norm_text and tracker.should_publish_event(track, norm_text):
                    # Save snapshot & plate crop evidence
                    snap_url, crop_url = self.storage.save_evidence(frame, plate_crop, camera_id)

                    # Publish ANPR Detection Event to Redis Stream
                    await self.publisher.publish_anpr_event(
                        camera_id=camera_id,
                        vehicle_type=track.vehicle_type,
                        vehicle_confidence=track.confidence,
                        track_id=track.track_id,
                        raw_plate=raw_text,
                        normalised_plate=norm_text,
                        plate_confidence=ocr_conf,
                        snapshot_url=snap_url,
                        plate_crop_url=crop_url,
                        pts_ms=pts_ms,
                    )

        # 4. Periodically publish camera health
        await self.publisher.publish_health_event(camera_id=camera_id, online=True)

    async def run(self):
        """Starts stream workers and enters main event loop."""
        self.is_running = True
        await self.publisher.connect()
        logger.info("Sentinel AI Stream Engine is ready and running.")

        ingest_mgr = StreamIngestionManager()
        cameras = await ingest_mgr.fetch_camera_configs()

        tasks = []
        for cam in cameras:
            if cam.get("enabled", True):
                worker = RTSPStreamWorker(
                    camera_id=cam["camera_id"],
                    rtsp_url=cam["rtsp_url"],
                    frame_callback=self.process_frame,
                )
                tasks.append(asyncio.create_task(worker.start()))

        if not tasks:
            logger.warning("No active camera streams found. Starting background health loop...")

        while self.is_running:
            await asyncio.sleep(1)


async def main():
    engine = SentinelAIEngine()
    await engine.run()


if __name__ == "__main__":
    asyncio.run(main())
