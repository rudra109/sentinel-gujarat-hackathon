"""
Person A — Multi-Object Tracker & Deduplicator (Module A5)
Manages within-camera persistent object tracks, multi-frame OCR consensus,
and 30-second observation deduplication per vehicle track ID.
"""
import time
import logging
from typing import Dict, Any, List, Optional
import numpy as np

logger = logging.getLogger("tracker")


def compute_iou(boxA: List[int], boxB: List[int]) -> float:
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[0])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[0])

    iou = interArea / float(boxAArea + boxBArea - interArea + 1e-5)
    return iou


class TrackedVehicle:
    def __init__(self, track_id: int, bbox: List[int], vehicle_type: str, confidence: float):
        self.track_id = track_id
        self.bbox = bbox
        self.vehicle_type = vehicle_type
        self.confidence = confidence
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.ocr_history: List[Dict[str, Any]] = []
        self.last_published_time: float = 0.0
        self.last_published_plate: str = ""

    def update_ocr(self, raw_plate: str, norm_plate: str, conf: float, snapshot: Any, plate_crop: Any):
        self.last_seen = time.time()
        if norm_plate:
            self.ocr_history.append({
                "raw": raw_plate,
                "norm": norm_plate,
                "conf": conf,
                "snapshot": snapshot,
                "plate_crop": plate_crop,
                "time": time.time()
            })

    def get_best_reading(self) -> Optional[Dict[str, Any]]:
        """Multi-frame consensus: returns the highest-confidence valid reading from track history."""
        if not self.ocr_history:
            return None
        return max(self.ocr_history, key=lambda x: x["conf"])


class CameraTracker:
    def __init__(self, camera_id: str, dedup_window: float = 30.0):
        self.camera_id = camera_id
        self.dedup_window = dedup_window
        self.next_track_id = 100
        self.tracks: Dict[int, TrackedVehicle] = {}

    def update_tracks(self, detections: List[Any]) -> List[TrackedVehicle]:
        """Updates tracks using IoU matching and returns active TrackedVehicle objects."""
        current_time = time.time()
        updated_vehicles = []

        # Remove stale tracks older than 60s
        stale_ids = [tid for tid, trk in self.tracks.items() if (current_time - trk.last_seen) > 60]
        for tid in stale_ids:
            del self.tracks[tid]

        for det in detections:
            matched_id = None
            best_iou = 0.3  # Minimum IoU threshold

            for tid, trk in self.tracks.items():
                iou = compute_iou(det.bbox, trk.bbox)
                if iou > best_iou:
                    best_iou = iou
                    matched_id = tid

            if matched_id is not None:
                trk = self.tracks[matched_id]
                trk.bbox = det.bbox
                trk.confidence = max(trk.confidence, det.confidence)
                trk.last_seen = current_time
            else:
                matched_id = self.next_track_id
                self.next_track_id += 1
                trk = TrackedVehicle(matched_id, det.bbox, det.label, det.confidence)
                self.tracks[matched_id] = trk

            updated_vehicles.append(trk)

        return updated_vehicles

    def should_publish_event(self, track: TrackedVehicle, norm_plate: str) -> bool:
        """
        Deduplication rule: Avoid spamming duplicate events.
        Publishes if track hasn't published within `dedup_window` seconds,
        or if a distinctly new plate reading was recognized.
        """
        now = time.time()
        if not norm_plate:
            return False

        if (now - track.last_published_time) >= self.dedup_window or track.last_published_plate != norm_plate:
            track.last_published_time = now
            track.last_published_plate = norm_plate
            return True

        return False
