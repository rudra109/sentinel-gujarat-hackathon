"""
Person A — Evidence Storage Manager (Module A7)
Saves full-frame JPEG snapshots and cropped license plate images for event evidence.
"""
import os
import uuid
import time
import logging
from typing import Tuple, Optional
import numpy as np
import cv2

logger = logging.getLogger("evidence-storage")


class EvidenceStorage:
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            storage_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "api", "static", "evidence")
            )
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.info(f"Evidence storage initialized at: {self.storage_dir}")

    def save_evidence(self, frame: np.ndarray, plate_crop: np.ndarray, camera_id: str) -> Tuple[str, str]:
        """
        Saves full snapshot and plate crop to disk.
        Returns: Tuple of (snapshot_relative_url, plate_crop_relative_url)
        """
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        uid = uuid.uuid4().hex[:8]

        snapshot_filename = f"{camera_id}_{timestamp_str}_{uid}_snap.jpg"
        crop_filename = f"{camera_id}_{timestamp_str}_{uid}_plate.jpg"

        snapshot_path = os.path.join(self.storage_dir, snapshot_filename)
        crop_path = os.path.join(self.storage_dir, crop_filename)

        try:
            if frame is not None and frame.size > 0:
                cv2.imwrite(snapshot_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])

            if plate_crop is not None and plate_crop.size > 0:
                cv2.imwrite(crop_path, plate_crop, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        except Exception as e:
            logger.error(f"Error writing evidence image files: {e}")

        # Return static URLs accessible by Person B frontend
        snap_url = f"/static/evidence/{snapshot_filename}"
        crop_url = f"/static/evidence/{crop_filename}"

        return snap_url, crop_url
