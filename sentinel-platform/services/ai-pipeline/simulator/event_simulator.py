"""
Person A — Live AI Stream & Event Simulator CLI
Simulates multi-camera RTSP stream detections and publishes realistic Indian vehicle ANPR events
and camera health events to Redis Streams. Tests end-to-end watchlist matching, GIS movement,
and WebSocket alert popups on Person B's command centre.
"""
import sys
import os
import time
import random
import asyncio
import logging
import numpy as np
import cv2

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from publisher.redis_publisher import RedisEventPublisher
from evidence.storage import EvidenceStorage
from models.ocr_engine import PlateOCREngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ai-simulator")

# Realistic sample Gujarati & Indian vehicle number plates
SAMPLE_PLATES = [
    ("GJ01AB1234", "car"),
    ("GJ05CD5678", "car"),
    ("GJ18EF9012", "truck"),
    ("GJ06GH3456", "motorcycle"),
    ("MH12IJ7890", "car"),
    ("GJ27KL1122", "bus"),
    ("GJ03MN3344", "car"),
]

# Preset Camera Locations across Gujarat
CAMERAS = [
    {"id": "CAM-01", "name": "SG Highway Junction (Ahmedabad)", "lat": 23.0225, "lon": 72.5714},
    {"id": "CAM-02", "name": "Ashram Road Intersection", "lat": 23.0330, "lon": 72.5650},
    {"id": "CAM-03", "name": "Gandhinagar CH-3 Circle", "lat": 23.2156, "lon": 72.6369},
    {"id": "CAM-04", "name": "Surat Ring Road Toll Gate", "lat": 21.1702, "lon": 72.8311},
    {"id": "CAM-05", "name": "Vadodara Alkapuri Flyover", "lat": 22.3072, "lon": 73.1812},
]


def generate_synthetic_images(plate_text: str, vehicle_type: str):
    """Generates realistic vehicle snapshot and plate crop images in memory."""
    # Full Frame Snapshot (800x450 dark CCTV view)
    frame = np.zeros((450, 800, 3), dtype=np.uint8)
    frame[:] = (30, 35, 45)

    # Road line overlay
    cv2.line(frame, (0, 300), (800, 300), (80, 85, 95), 3)
    cv2.putText(frame, f"LIVE CCTV FEED — {vehicle_type.upper()}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 200), 2)
    cv2.putText(frame, time.strftime("%Y-%m-%d %H:%M:%S IST"), (520, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    # Vehicle Bounding Box
    cv2.rectangle(frame, (250, 180), (550, 380), (0, 220, 100), 2)
    cv2.putText(frame, f"{vehicle_type} 94%", (255, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 100), 2)

    # License Plate Box inside Vehicle
    cv2.rectangle(frame, (350, 310), (470, 350), (255, 255, 255), -1)
    cv2.rectangle(frame, (350, 310), (470, 350), (0, 0, 255), 2)
    cv2.putText(frame, plate_text, (355, 338), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)

    # Plate Crop Image (240x80 high-res plate crop)
    plate_crop = np.zeros((80, 240, 3), dtype=np.uint8)
    plate_crop[:] = (245, 245, 245)
    cv2.rectangle(plate_crop, (4, 4), (236, 76), (10, 10, 10), 3)
    cv2.putText(plate_crop, "IND", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 0, 0), 2)
    cv2.putText(plate_crop, plate_text, (55, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)

    return frame, plate_crop


async def run_simulator(interval: float = 3.0, iterations: int = 100):
    logger.info("==================================================================")
    logger.info("  Sentinel Person A — AI Stream & Event Simulator Starting  ")
    logger.info("==================================================================")

    publisher = RedisEventPublisher()
    await publisher.connect()
    storage = EvidenceStorage()
    ocr_engine = PlateOCREngine(use_easyocr=False)

    track_id_counter = 100

    try:
        for i in range(iterations):
            cam = random.choice(CAMERAS)
            plate_text, vehicle_type = random.choice(SAMPLE_PLATES)
            track_id_counter += 1

            # Perform OCR normalization & validation
            raw_plate = plate_text
            norm_plate = ocr_engine.normalize_plate(raw_plate)
            conf = round(random.uniform(0.88, 0.98), 2)

            # Generate synthetic frame snapshot & plate crop
            frame, plate_crop = generate_synthetic_images(norm_plate, vehicle_type)
            snap_url, crop_url = storage.save_evidence(frame, plate_crop, cam["id"])

            # 1. Publish ANPR Event
            msg_id = await publisher.publish_anpr_event(
                camera_id=cam["id"],
                vehicle_type=vehicle_type,
                vehicle_confidence=0.94,
                track_id=track_id_counter,
                raw_plate=raw_plate,
                normalised_plate=norm_plate,
                plate_confidence=conf,
                snapshot_url=snap_url,
                plate_crop_url=crop_url,
                lat=cam["lat"],
                lon=cam["lon"]
            )

            # 2. Publish Camera Health Event
            await publisher.publish_health_event(
                camera_id=cam["id"],
                online=True,
                blur_score=round(random.uniform(75, 95), 1),
                brightness_score=round(random.uniform(100, 140), 1),
                latency_ms=round(random.uniform(30, 60), 1)
            )

            logger.info(f"[{i+1}/{iterations}] Event sent -> Cam: {cam['id']} ({cam['name']}) | Plate: {norm_plate} | Track: #{track_id_counter}")

            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Simulator stopped by user.")
    finally:
        await publisher.close()
        logger.info("Publisher disconnected.")


if __name__ == "__main__":
    interval_sec = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
    asyncio.run(run_simulator(interval=interval_sec))
