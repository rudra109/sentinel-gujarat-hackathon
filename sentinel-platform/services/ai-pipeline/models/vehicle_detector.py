"""
Person A — Vehicle Detector (Model A)
Detects vehicles in CCTV frames using Ultralytics YOLO with fallback detection support.
"""
import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger("vehicle-detector")


class Detection:
    def __init__(self, bbox: List[int], label: str, confidence: float, crop: np.ndarray):
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.label = label
        self.confidence = confidence
        self.crop = crop


class VehicleDetector:
    def __init__(self, model_path: str = "yolov8n.pt", conf_thresh: float = 0.4):
        self.conf_thresh = conf_thresh
        self.yolo_model = None
        self.target_classes = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

        try:
            from ultralytics import YOLO
            self.yolo_model = YOLO(model_path)
            logger.info(f"YOLO Vehicle Detector loaded successfully: {model_path}")
        except Exception as e:
            logger.warning(f"Could not load YOLO model ({e}). Using heuristic fallback vehicle detector.")

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Detect vehicles in frame. Returns list of Detection objects."""
        if frame is None or frame.size == 0:
            return []

        detections = []
        h, w = frame.shape[:2]

        if self.yolo_model is not None:
            try:
                results = self.yolo_model(frame, verbose=False, conf=self.conf_thresh)[0]
                for box in results.boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    if cls_id in self.target_classes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        x1, y1 = max(0, x1), max(0, y1)
                        x2, y2 = min(w, x2), min(h, y2)
                        crop = frame[y1:y2, x1:x2]
                        if crop.size > 0:
                            label = self.target_classes[cls_id]
                            detections.append(Detection([x1, y1, x2, y2], label, conf, crop))
                return detections
            except Exception as e:
                logger.error(f"YOLO inference error: {e}")

        # Fallback Heuristic Vehicle Detection (Grid/Contour-based)
        import cv2
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > (w * h * 0.02):  # Significant object size
                x, y, bw, bh = cv2.boundingRect(cnt)
                x1, y1, x2, y2 = x, y, x + bw, y + bh
                crop = frame[y1:y2, x1:x2]
                if crop.size > 0:
                    aspect_ratio = bw / float(bh) if bh > 0 else 1.0
                    label = "bus" if aspect_ratio > 2.0 else ("motorcycle" if aspect_ratio < 0.8 else "car")
                    detections.append(Detection([x1, y1, x2, y2], label, 0.85, crop))

        return detections
