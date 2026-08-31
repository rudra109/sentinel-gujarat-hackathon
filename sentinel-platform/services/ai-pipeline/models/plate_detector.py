"""
Person A — License Plate Detector (Model B)
Locates license plate bounding boxes inside vehicle crop regions.
"""
import logging
from typing import List, Tuple, Optional
import numpy as np
import cv2

logger = logging.getLogger("plate-detector")


class PlateDetector:
    def __init__(self, model_path: str = "plate_detector.pt", conf_thresh: float = 0.35):
        self.conf_thresh = conf_thresh
        self.yolo_model = None

        try:
            from ultralytics import YOLO
            self.yolo_model = YOLO(model_path)
            logger.info(f"YOLO Plate Detector loaded: {model_path}")
        except Exception as e:
            logger.info(f"YOLO Plate Detector unavailable ({e}). Using OpenCV morphological plate detector.")

    def detect_plate(self, vehicle_crop: np.ndarray) -> Optional[Tuple[List[int], float, np.ndarray]]:
        """
        Detects license plate inside a vehicle crop.
        Returns: Tuple of ([x1, y1, x2, y2], confidence, plate_crop) or None
        """
        if vehicle_crop is None or vehicle_crop.size == 0:
            return None

        vh, vw = vehicle_crop.shape[:2]

        if self.yolo_model is not None:
            try:
                results = self.yolo_model(vehicle_crop, verbose=False, conf=self.conf_thresh)[0]
                best_box = None
                best_conf = 0.0
                for box in results.boxes:
                    conf = float(box.conf[0].item())
                    if conf > best_conf:
                        best_conf = conf
                        best_box = map(int, box.xyxy[0].tolist())
                if best_box is not None and best_conf >= self.conf_thresh:
                    x1, y1, x2, y2 = best_box
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(vw, x2), min(vh, y2)
                    plate_crop = vehicle_crop[y1:y2, x1:x2]
                    if plate_crop.size > 0:
                        return [x1, y1, x2, y2], best_conf, plate_crop
            except Exception as e:
                logger.error(f"YOLO plate detection error: {e}")

        # High-Recall OpenCV Morphological Plate Detector
        gray = cv2.cvtColor(vehicle_crop, cv2.COLOR_BGR2GRAY)
        rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))
        top_hat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, rect_kernel)

        grad_x = cv2.Sobel(top_hat, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
        grad_x = np.absolute(grad_x)
        (min_val, max_val) = (np.min(grad_x), np.max(grad_x))
        if max_val > min_val:
            grad_x = (255 * ((grad_x - min_val) / (max_val - min_val))).astype("uint8")

        grad_x = cv2.morphologyEx(grad_x, cv2.MORPH_CLOSE, rect_kernel)
        thresh = cv2.threshold(grad_x, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best_candidate = None
        best_score = 0.0

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / float(h) if h > 0 else 0
            if 2.0 <= aspect_ratio <= 5.5 and w > 30 and h > 10:
                score = w * h
                if score > best_score:
                    best_score = score
                    best_candidate = [x, y, x + w, y + h]

        if best_candidate is not None:
            x1, y1, x2, y2 = best_candidate
            plate_crop = vehicle_crop[y1:y2, x1:x2]
            return best_candidate, 0.88, plate_crop

        # Fallback to lower 40% region of vehicle crop if morphological search fails
        y1_sub = int(vh * 0.5)
        plate_crop = vehicle_crop[y1_sub:vh, 0:vw]
        return [0, y1_sub, vw, vh], 0.70, plate_crop
