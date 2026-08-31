# Person A — Sentinel AI Stream Engine & Inference Pipeline

> **Gujarat Police Innovation Hackathon 2026**  
> **Module Owner:** Person A (AI / Video / Stream Engine)

---

## Architecture Overview

```
RTSP CCTV Stream
       │
       ▼
Stream Reader (Adaptive Sampling + Exponential Backoff)
       │
       ▼
Model A: Vehicle Detector (YOLO / OpenCV)
       │
       ▼
Within-Camera Multi-Object Tracker (ByteTrack / IoU Track)
       │
       ▼
Model B: License Plate Detector (YOLO / Morphological)
       │
       ▼
Model C: ANPR OCR Engine (EasyOCR / Grammar Rules)
       │
       ▼
ANPR Post-Processor (Normalization + Consensus + 30s Dedup)
       │
       ▼
Evidence Storage (High-Res Snapshot + Plate Crop JPEGs)
       │
       ▼
Redis Event Publisher (`sentinel:ai:events` & `sentinel:health:events`)
```

---

## Key Person A Components Built

| Component | File | Description |
|---|---|---|
| **Vehicle Detector** | `models/vehicle_detector.py` | Detects cars, trucks, buses, motorcycles, auto-rickshaws. |
| **Plate Detector** | `models/plate_detector.py` | Locates 1-class license plates inside vehicle crops. |
| **ANPR OCR Engine** | `models/ocr_engine.py` | Text recognition, Indian plate grammar validation, character confusion fixing (`O`↔`0`, `I`↔`1`). |
| **Tracker & Dedup** | `tracking/tracker.py` | Persistent track IDs, multi-frame consensus reading, 30-second observation deduplication window. |
| **Evidence Storage** | `evidence/storage.py` | Saves snapshots & plate crop JPEGs to `/static/evidence/`. |
| **Redis Publisher** | `publisher/redis_publisher.py` | Publishes standard JSON events matching Person B contract to Redis streams. |
| **RTSP Stream Reader** | `ingest/stream_reader.py` | Dynamic camera sync from backend, RTSP TCP decoding, auto-reconnect backoff. |
| **AI Stream Simulator** | `simulator/event_simulator.py` | Standalone CLI simulator pushing live Gujarati/Indian vehicle detection events. |
| **Performance Benchmark**| `benchmark.py` | Benchmark measuring latency (ms), FPS throughput, and memory usage. |
| **Pipeline Main** | `pipeline_main.py` | Production entry point orchestrating all AI components. |

---

## How to Run

### 1. Run AI Performance Benchmark
```bash
python services/ai-pipeline/benchmark.py
```

### 2. Run AI Event Simulator (Generates live Gujarati vehicle detections)
```bash
python services/ai-pipeline/simulator/event_simulator.py 2.0
```

### 3. Run Production AI Stream Engine
```bash
python services/ai-pipeline/pipeline_main.py
```
