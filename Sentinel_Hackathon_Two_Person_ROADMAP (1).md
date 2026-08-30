# Sentinel Unified Intelligence Platform
## Two-Person Development Roadmap for Gujarat Police Innovation Hackathon 2026

> **Project strategy:** Hybrid architecture combining the mandatory **Model 1 CCTV Registry + GIS**, the working live-view capabilities of **Model 2**, the adapter/event architecture of **Model 3**, and selected high-value AI/VMS functions from **Model 4**.
>
> **Core operating loop:** **LIVE → DETECT → RECOGNISE → CORRELATE → ALERT → INVESTIGATE**
>
> **Primary evaluation objective:** A real working system on the official Sentinel sandbox feeds, not a mock UI.

---

# 1. Project Goal

Build a deployment-oriented CCTV intelligence platform that can:

1. Discover and onboard the official Sentinel sandbox cameras dynamically.
2. Maintain a central CCTV registry with GIS metadata.
3. View multiple live feeds through one control-room interface.
4. Process live RTSP feeds with AI.
5. Detect vehicles.
6. Detect and read Indian vehicle number plates.
7. Store timestamped camera/location detections.
8. Continuously compare recognised plates against a watchlist.
9. Generate real-time alerts when a match occurs.
10. Correlate the same vehicle across multiple cameras.
11. Reconstruct an observed CCTV movement path on GIS.
12. Provide searchable investigation history and evidence.
13. Monitor camera/stream health.
14. Provide RBAC and audit logs.
15. Demonstrate a technically credible path from the sandbox scale to approximately 80,000 cameras.

The project should **not** attempt to recreate every commercial VMS feature. The focus is the strongest end-to-end law-enforcement intelligence workflow.

---

# 2. Official Challenge Alignment

The solution maps to the official reference models as follows.

## Model 1 — Mandatory Foundation

Use almost completely:

- Central CCTV Registry
- GIS camera mapping
- Camera metadata
- Dynamic onboarding
- Camera health/status
- Search/filter/export
- Audit trail
- Role-based access
- Gap/coverage reporting

## Model 2 — Unified Viewing + Analytics

Use almost completely:

- Unified live viewer
- Multi-camera grid
- Live stream consumption
- ANPR-generated metadata
- Camera-wise event indexing
- Searchable vehicle movement records
- Alerts for vehicles of interest

## Model 3 — Federation / Middleware Concepts

Use the strongest architecture ideas:

- Connector / adapter interface
- Protocol abstraction
- Standard internal camera schema
- Standard AI event schema
- Event/message bus
- Extensible connector framework
- Cross-system correlation
- Unified downstream API

Do **not** spend the entire hackathon building full enterprise VMS federation.

## Model 4 — Selected High-Value Capabilities

Build:

- Central stream ingestion prototype
- Vehicle detection
- ANPR
- Multi-location vehicle tracking
- Watchlist matching
- Real-time alerts
- Evidence snapshot/clip management
- Searchable intelligence
- GIS route reconstruction
- Central command dashboard
- Security design
- Redundancy design
- Scalability/load-test plan
- GPU inference architecture

Do not initially build:

- Full 24×7 central recording of every camera
- Huge hot/warm/cold production storage cluster
- Complete replacement for enterprise VMS products
- Facial recognition as a dependency
- Every possible CCTV analytics model

---

# 3. Current Sentinel Sandbox Integration Facts

The official resource guide states that sandbox cameras are live streams.

Supported access patterns include:

- **RTSP / RTP:** intended for AI inference
- **WebRTC / WHEP:** low-latency browser viewing
- **HLS:** dashboard/mobile/restricted-network viewing
- **Camera catalogue API:** `/api/ingest`

The system must **never hard-code the current camera count or IDs**.

The current portal may show around 30 cameras, while the official technical problem describes approximately 50 heterogeneous feeds for evaluation. The camera catalogue is therefore the source of truth.

## Required Stream Rules

Every implementation must:

- Read available cameras dynamically from `/api/ingest`.
- Prefer RTSP-over-TCP for AI workers.
- Use HLS or WebRTC for browser viewing where appropriate.
- Handle both H.264 and H.265.
- Handle mixed resolutions and bitrates.
- Not trust reported FPS.
- Use stream PTS/timestamps for timing.
- Tolerate irregular frame intervals.
- Reconnect automatically with exponential backoff.
- Treat decoder warnings during stream join as recoverable.
- Recover from scene discontinuities/loop points.
- Avoid downloading footage as files.
- Avoid opening unnecessary streams simultaneously.
- Close streams that are no longer being processed.

---

# 4. AI/ML Models to Train

## 4.1 Model A — Vehicle Detector

### Purpose

Detect vehicles before sending smaller vehicle regions to the number-plate model.

### Recommended Model

**YOLO26s** as the main starting point.

Fallback if deployment compatibility becomes an issue:

**YOLO11s**

### Train / Fine-Tune For

Recommended classes:

- car
- motorcycle
- bus
- truck
- auto-rickshaw / three-wheeler if the dataset supports it

Do not create too many classes.

### Dataset Type

Use Indian road/CCTV vehicle datasets from Kaggle or other legally usable sources.

Prefer data containing:

- CCTV viewpoints
- high-angle traffic cameras
- day/night samples
- low-resolution vehicles
- motion blur
- occlusion
- Indian traffic density

### Why It Is Needed

The general detector reduces computation because number-plate detection runs only on detected vehicle crops rather than the whole frame.

### Output

For each object:

- bounding box
- vehicle class
- detection confidence
- temporary track ID

### Metric

Track:

- mAP50-95
- recall
- precision
- small-object performance
- real-time inference latency

---

# 4.2 Model B — Licence Plate Detector

### Purpose

Locate a number plate inside each detected vehicle crop.

### Recommended Model

**YOLO26s** trained as a separate one-class detector.

Class:

- `license_plate`

A smaller YOLO26n may be benchmarked later for speed.

### Why Separate It From Vehicle Detection

Plates are small objects.

Pipeline:

`Full frame → Vehicle Detector → Vehicle Crop → Plate Detector`

This is usually more computationally efficient and allows the plate detector to work with much larger effective plate resolution.

### Dataset Type

Use Indian number-plate detection datasets.

Include:

- front plates
- rear plates
- white plates
- yellow commercial plates
- angled plates
- blurred plates
- night plates
- partially occluded plates
- low-resolution CCTV plates

### Metric

The most important metric is **plate recall**.

Missing a plate completely is worse than returning an imperfect crop.

---

# 4.3 Model C — Number Plate OCR / Recognition

### Purpose

Convert the cropped number-plate image into text.

Example:

`plate crop → GJ05AB1234`

### Recommended Model

Fine-tune a lightweight **PaddleOCR PP-OCRv5 recognition model** for Indian number plates.

Prefer the mobile/lightweight recogniser for live multi-camera inference.

Benchmark a server model only if accuracy improvement is significant enough to justify latency.

### Character Vocabulary

For the initial recogniser:

- A-Z
- 0-9

No unnecessary punctuation.

### Training Data

Use labelled plate crops where the exact number is known.

Add augmentation for:

- motion blur
- Gaussian blur
- low light
- glare
- compression
- perspective distortion
- low contrast
- partial dirt
- small resolution

### Post-Processing

Use Indian plate grammar carefully.

Examples:

- `GJ05AB1234`
- `MH12XX1234`

Do not automatically force every OCR result into a legal format.

Instead return:

- raw OCR
- normalised OCR
- OCR confidence
- format-valid flag

Common ambiguous characters:

- O / 0
- I / 1
- B / 8
- S / 5
- Z / 2

Use contextual correction only when confidence supports it.

### Watchlist Matching Rule

For critical alerts:

- exact normalised plate match = strong alert
- near match = possible match / operator verification
- never silently convert a weak OCR result into a confirmed alert

### Metrics

Track:

- character accuracy
- character error rate
- full-plate exact-match accuracy
- end-to-end ANPR accuracy on CCTV frames

---

# 4.4 Model D — Vehicle Re-Identification (High-Value Bonus)

### Priority

**Train only after Models A, B and C work well.**

### Purpose

Help correlate a vehicle when:

- plate is unreadable
- plate is temporarily occluded
- image is too blurred
- only some cameras capture the plate clearly

### Recommended Approach

Use **FastReID** with a strong vehicle-ReID configuration such as an R50-IBN/SBS or equivalent baseline.

Train/fine-tune on a vehicle-ReID dataset such as:

- VeRi-776
- VehicleID
- VERI-Wild

If using a Kaggle mirror, verify the original dataset licence.

### Output

A vehicle embedding vector.

Cross-camera candidate score can combine:

- plate similarity
- ReID similarity
- vehicle type
- colour
- camera/time plausibility

### Important

ReID is a **fallback intelligence signal**.

The primary identity remains the number plate whenever a reliable plate is available.

---

# 4.5 Optional Model E — Vehicle Attribute Classifier

### Priority

Optional.

### Purpose

Classify:

- colour
- broad vehicle category

### Recommendation

Do not build this until the core ANPR pipeline works.

Vehicle category already comes from Model A.

Colour can initially be estimated using simpler image logic or a small classifier.

Potential model:

- YOLO26n-cls
- EfficientNet-B0

### Benefit

Useful for:

- validating OCR matches
- narrowing vehicle search
- improving ReID confidence

---

# 4.6 Models We Should NOT Train Initially

Do not spend time training these for Phase 1:

- facial recognition
- weapon detection
- fire detection
- violence detection
- helmet detection
- person ReID
- crowd anomaly detection
- generic suspicious-behaviour model
- speed-estimation model

These can be future modules.

The official evaluation is better served by a highly reliable ANPR + cross-camera workflow.

---

# 5. Features That Need NO New ML Model

These are software problems, not model-training problems.

## Within-Camera Tracking

Use:

- ByteTrack
- or BoT-SORT

No custom training required.

## Watchlist

Database lookup.

No training.

## Real-Time Alerting

Rules/event engine.

No training.

## Cross-Camera Correlation

Start with:

- plate string
- camera
- timestamp
- location

Then add ReID as a secondary signal.

## GIS Route Reconstruction

PostGIS/map logic.

No training.

## Camera Offline Detection

Stream health logic.

No training.

## Camera Freeze Detection

Frame similarity / timestamp checks.

No training.

## Dark / Overexposed Camera Detection

Histogram/brightness thresholds.

No training.

## Blur Detection

Focus/edge metrics.

No training.

## Intrusion Zone

Vehicle/person detector + polygon rule.

No extra model.

## Crowd Count

Existing person detector + tracker/counting.

No dedicated crowd model required for the initial prototype.

## RBAC

Application logic.

## Audit Logs

Application logic.

---

# 6. Final AI Pipeline

```text
Official RTSP Camera
        |
        v
Frame Decoder
        |
        v
Adaptive Frame Sampler
        |
        v
Vehicle Detector
        |
        +--------------------------+
        |                          |
        v                          v
Within-Camera Tracker       Vehicle Crop
                                   |
                                   v
                           Plate Detector
                                   |
                                   v
                              Plate Crop
                                   |
                                   v
                              OCR Model
                                   |
                                   v
                       Normalise + Confidence
                                   |
                                   v
                          Event Generation
                                   |
                 +-----------------+----------------+
                 |                                  |
                 v                                  v
          Watchlist Match                    Detection DB
                 |                                  |
                 v                                  v
            Alert Engine                 Cross-Camera Correlation
                                                    |
                                                    v
                                            Vehicle Timeline
                                                    |
                                                    v
                                              GIS Movement
```

---

# 7. Real-Time Compute Strategy

Do not run every expensive model at full camera FPS.

## Efficient Flow

1. Decode the live stream.
2. Use adaptive frame sampling.
3. Run the vehicle detector.
4. Track vehicles.
5. Run the plate detector only on vehicle crops.
6. Run OCR only when a usable plate crop exists.
7. Run OCR across a few frames of the same track and choose the best/consensus reading.
8. Deduplicate repeated detections.
9. Generate an event only when necessary.

## Deduplication Example

The same vehicle may appear in 50 consecutive frames.

Do not create 50 database events.

Create one camera observation with:

- first seen
- last seen
- best plate crop
- best OCR
- confidence
- representative snapshot

---

# 8. Project Architecture

```text
                    SENTINEL SANDBOX
                           |
              +------------+------------+
              |                         |
             RTSP                    HLS/WebRTC
              |                         |
              v                         v
       STREAM WORKER               WEB VIEWER
              |
              v
       AI INFERENCE LAYER
              |
              v
        STANDARD EVENT BUS
              |
      +-------+---------+--------------------+
      |                 |                    |
      v                 v                    v
 WATCHLIST          EVENT DB            HEALTH ENGINE
      |                 |                    |
      v                 v                    v
 ALERT ENGINE       CORRELATION         CAMERA STATUS
      |                 |
      +--------+--------+
               |
               v
            API LAYER
               |
      +--------+----------+
      |                   |
      v                   v
  COMMAND UI           GIS / SEARCH
```

---

# 9. Recommended Technology Stack

The exact stack can change if the team is already stronger in another technology.

## Frontend

- React
- Vite or Next.js
- HLS.js for HLS viewing
- WebRTC/WHEP integration where useful
- Leaflet or OpenLayers for GIS
- WebSocket/SSE for live alerts

## Backend

Recommended:

- FastAPI
- Python

Reason:

- easier integration with AI services
- strong async API support
- fewer language boundaries for a two-person team

## Database

- PostgreSQL
- PostGIS

Tables include:

- cameras
- camera_health
- detections
- vehicle_observations
- watchlists
- alerts
- evidence
- users
- roles
- audit_logs

## Cache / Messaging

Prototype:

- Redis
- Redis Streams or lightweight queue

Production architecture document may show:

- Kafka/RabbitMQ
- partitioned event processing

Do not introduce Kafka merely to look advanced if it slows development.

## Evidence Storage

Prototype:

- filesystem or MinIO/S3-compatible object storage

Store only event evidence:

- snapshots
- plate crops
- short clips where practical

Do not centrally record every feed continuously during Phase 1.

## AI Runtime

Initial:

- Python
- PyTorch
- OpenCV / FFmpeg / GStreamer

Optimised option:

- ONNX Runtime
- TensorRT
- NVIDIA DeepStream

Only move to DeepStream/TensorRT after the baseline works.

---

# 10. Main Database Entities

## Camera

```text
id
external_camera_id
name
department
district
location_text
latitude
longitude
codec
resolution
bitrate
rtsp_url
hls_url
webrtc_url
live_status
ai_status
created_at
updated_at
```

## Vehicle Observation

```text
id
camera_id
track_id
vehicle_type
plate_raw
plate_normalised
plate_confidence
vehicle_detection_confidence
first_seen_pts
last_seen_pts
observed_at
latitude
longitude
snapshot_path
plate_crop_path
reid_embedding_ref
```

## Watchlist

```text
id
plate_number
category
priority
reason
active
created_by
created_at
expires_at
```

Example categories:

- stolen
- suspect
- investigation
- blacklisted
- test-target

## Alert

```text
id
observation_id
watchlist_id
severity
status
created_at
acknowledged_by
acknowledged_at
notes
```

## Camera Health

```text
camera_id
online
last_frame_pts
latency
codec
resolution
blur_score
brightness_score
freeze_status
last_checked_at
```

## Audit Log

```text
id
user_id
action
entity_type
entity_id
metadata
timestamp
```

---

# 11. Standard Event Contract

Every AI/stream worker should publish a consistent event.

Example:

```json
{
  "event_id": "uuid",
  "event_type": "ANPR_DETECTION",
  "camera_id": "CAM-07",
  "pts_ms": 12345678,
  "observed_at": "timestamp",
  "location": {
    "lat": 0.0,
    "lon": 0.0
  },
  "vehicle": {
    "type": "car",
    "confidence": 0.94,
    "track_id": 181
  },
  "plate": {
    "raw": "GJO5ABI234",
    "normalised": "GJ05AB1234",
    "confidence": 0.91
  },
  "evidence": {
    "snapshot": "...",
    "plate_crop": "..."
  }
}
```

Person A and Person B must agree on this contract before integration.

---

# 12. Main Screens

## Screen 1 — Command Centre

Show:

- total cameras
- online/offline
- AI-active cameras
- active alerts
- recent detections
- Gujarat map
- system health
- quick vehicle search

## Screen 2 — Camera Registry

Features:

- list
- filters
- bulk onboarding
- manual camera entry
- dynamic sync from sandbox catalogue
- metadata
- live status
- AI status

## Screen 3 — GIS Camera Map

Pins:

- green = online
- red = offline
- orange = active alert
- yellow = degraded

Camera popup:

- name
- location
- department
- status
- watch live
- detections
- alerts
- health

## Screen 4 — Live Control Room

Grid:

- 4
- 9
- 16
- custom camera selection

Overlay:

- camera name
- online status
- AI active
- detected vehicles
- recognised plates
- watchlist alert

## Screen 5 — Watchlist

Features:

- add test target
- remove/deactivate
- set priority
- reason/category
- search
- audit

## Screen 6 — Alerts

Alert card:

- plate
- camera
- location
- timestamp
- confidence
- snapshot
- watch live
- evidence
- track vehicle
- acknowledge

## Screen 7 — Vehicle Investigation

Input:

- plate number

Output:

- total observations
- first seen
- last seen
- cameras
- timestamps
- snapshots
- confidence
- timeline
- GIS path

## Screen 8 — Vehicle Journey

Map:

`Camera A → Camera B → Camera C`

Call it:

**Observed CCTV Movement Path**

Do not claim it is the exact driven road route unless a road-network routing engine is used.

## Screen 9 — Camera Health

Show:

- online
- offline
- reconnecting
- degraded
- frozen
- dark
- blurred
- codec/resolution
- last frame
- AI worker health

## Screen 10 — Audit Logs

Track:

- vehicle searches
- watchlist changes
- alert acknowledgement
- evidence views
- camera changes
- user/session actions

---

# 13. High-Value Demo Story

The final demo should tell one clear story.

## Step 1

Open the platform.

Show:

- camera catalogue successfully synced
- current live camera count
- system health

## Step 2

Open GIS.

Show the cameras at their mapped locations.

## Step 3

Open Control Room.

Show genuine Government sandbox feeds.

## Step 4

Show AI detection overlay.

Vehicles are being detected.

## Step 5

Add or receive the test vehicle registration number.

Example:

`GJ05AB1234`

## Step 6

Add it to the temporary evaluation watchlist if required.

## Step 7

The AI detects that plate on a real feed.

## Step 8

System automatically raises:

**WATCHLIST MATCH**

## Step 9

Open the alert.

Show:

- live camera
- snapshot
- plate crop
- timestamp
- camera
- location
- confidence

## Step 10

The same vehicle appears at another camera.

## Step 11

System correlates the new observation.

## Step 12

Open Vehicle Investigation.

Show the complete camera timeline.

## Step 13

Open GIS movement view.

Show observed movement:

`Camera A → Camera B → Camera C`

## Step 14

Show:

- camera health
- RBAC
- audit log

## Step 15

End with scale architecture:

`Sandbox → Pilot → Regional → Statewide 80,000+`

---

# 14. Cross-Camera Correlation Strategy

## Level 1 — Strongest

Exact normalised number plate.

## Level 2 — Supporting

Number plate similarity plus:

- time
- camera
- location
- vehicle type

## Level 3 — Bonus

Vehicle ReID embedding.

## Confidence Logic

Example:

```text
Exact plate + good OCR = HIGH confidence

Near plate + same vehicle type + plausible time = MEDIUM

No plate + strong ReID + plausible route = CANDIDATE only
```

Never label a low-confidence ReID-only result as a confirmed identity.

---

# 15. Camera Health Logic

Do not create a dedicated ML model unless later necessary.

Use software/CV checks.

## Offline

No frames after reconnect attempts.

## Freeze

Nearly identical frames across a configured period while timestamps advance.

## Dark

Mean/percentile brightness below threshold.

## Overexposed

Large percentage of pixels near maximum brightness.

## Blur

Laplacian/edge-based focus score.

## Decode Error

Track decoder failure rates.

## Scene Discontinuity

Reset:

- trackers
- temporal state
- background models
- ReID local galleries

when a hard cut/loop point is detected.

---

# 16. Security / Government Readiness

Implement in prototype:

- login
- JWT/session auth
- password hashing
- roles
- permission checks
- audit logs
- secure secret handling
- input validation
- rate limiting on sensitive endpoints
- evidence access controls

Document for production:

- TLS everywhere
- encryption at rest
- network segmentation
- VPN/private backbone
- zero-trust service access
- central identity integration
- SIEM logging
- secret vault
- key rotation
- HA
- DR
- security monitoring

---

# 17. RBAC Roles

Suggested roles:

## Super Admin

- all cameras
- users
- watchlists
- system config
- audit

## State Operator

- authorised statewide camera operations
- alerts
- investigations

## District Operator

- cameras for assigned district

## Department Operator

- cameras for assigned department

## Investigator

- search
- evidence
- journey
- alerts

## Viewer

- authorised view-only access

---

# 18. Scalability Architecture

Do not claim the prototype itself runs 80,000 live cameras.

Instead show how it scales.

## Sandbox

- 30–50 feeds
- 1–few GPU workers
- one PostgreSQL
- Redis
- local/MinIO evidence

## Pilot

- hundreds of cameras
- multiple stream workers
- GPU worker pool
- load-balanced API
- replicated database
- object storage

## Regional

- thousands of cameras
- regional ingest gateways
- edge AI where useful
- partitioned event bus
- regional caches
- central metadata platform

## Statewide

- approximately 80,000 cameras
- regional/edge ingest
- autoscaled GPU inference
- distributed event streaming
- distributed object storage
- HA Postgres/time-series/search layers
- disaster recovery site
- observability
- central command centre

---

# 19. Bandwidth Strategy

For production-scale planning:

- avoid relaying every stream centrally if not necessary
- perform selective analytics at regional/edge nodes
- transmit metadata instead of raw video whenever possible
- fetch live video on demand
- retain event evidence centrally
- adaptive bitrates for viewing
- use existing department storage where appropriate

This supports the challenge goal of using existing infrastructure rather than replacing everything.

---

# 20. Evidence Strategy

For Phase 1, store:

- best vehicle snapshot
- best plate crop
- metadata
- short event clip where feasible

Do not build continuous recording for every camera first.

A short event clip can include:

- a few seconds before detection
- detection moment
- a few seconds after

Evidence record must reference:

- camera
- timestamp/PTS
- detection
- watchlist match
- responsible user actions

---

# 21. Load / Performance Testing

Measure:

- number of concurrent feeds
- decode FPS
- inference FPS
- vehicle detector latency
- plate detector latency
- OCR latency
- end-to-end alert latency
- reconnect recovery time
- dropped frames
- CPU
- GPU
- RAM
- database event write rate

Produce a load-test report.

Do not fabricate 80,000-camera results.

Use measured sandbox performance plus transparent extrapolation and production architecture assumptions.

---

# 22. Development Ownership — Person A vs Person B

The two people should have clearly separated code ownership to avoid merge conflicts.

---

# PERSON A — AI / VIDEO / STREAM ENGINE

## Primary Mission

Make real Sentinel streams reliably produce accurate vehicle intelligence events.

## Owns

### A1. Model Training

Train/fine-tune:

- Vehicle Detector
- Licence Plate Detector
- Plate OCR
- Vehicle ReID if time permits
- Optional attribute classifier only after core success

### A2. Dataset Work

- dataset collection
- licensing check
- cleaning
- train/val/test split
- annotations
- augmentations
- class balance
- evaluation samples
- model comparison

### A3. Stream Reader

Build:

- `/api/ingest` camera discovery client
- RTSP TCP connection
- H.264/H.265 handling
- PTS extraction
- reconnect with exponential backoff
- scene-cut recovery
- dynamic camera enable/disable
- frame sampler

### A4. AI Inference Pipeline

Build:

`frame → vehicle → tracker → plate → OCR`

### A5. Tracking

Use ByteTrack or BoT-SORT.

Implement:

- within-camera persistent track
- best-frame selection
- observation deduplication

### A6. ANPR Post-Processing

Implement:

- normalisation
- confidence
- format check
- multi-frame consensus
- ambiguity handling

### A7. Evidence Generator

Generate:

- vehicle snapshot
- plate crop
- optional short clip
- model confidences

### A8. Standard AI Event Publisher

Publish events matching the agreed contract.

### A9. Vehicle ReID

If core pipeline is stable:

- train baseline
- expose embedding API
- return similarity candidates

### A10. AI Performance Report

Document:

- datasets
- metrics
- model versions
- validation results
- inference latency
- known failure cases

---

# PERSON B — PLATFORM / BACKEND / FRONTEND / GIS

## Primary Mission

Turn AI events and camera feeds into a usable police command and investigation system.

## Owns

### B1. Project Backend

Build:

- FastAPI backend
- authentication
- API structure
- WebSocket/SSE events
- validation
- logging

### B2. Database

Design and implement:

- PostgreSQL
- PostGIS
- migrations
- camera tables
- event tables
- watchlists
- alerts
- evidence
- users
- roles
- audit logs

### B3. Camera Registry

Build:

- dynamic camera sync
- registry table
- manual onboarding
- CSV bulk import
- filters
- metadata views

### B4. GIS

Build:

- camera map
- location pins
- online/offline/alert states
- camera detail popup
- vehicle journey map

### B5. Live Control Room

Use:

- HLS and/or WHEP browser streams
- selectable multi-camera grids
- live event overlay
- alert indicators

### B6. Watchlist Engine

Implement:

- CRUD
- exact normalised match
- possible-match handling
- severity
- expiration
- audit

### B7. Alert Engine

Implement:

- live alerts
- severity
- acknowledgment
- alert history
- linked evidence
- vehicle tracking button

### B8. Investigation Search

Search:

- plate
- time range
- camera
- district
- department
- confidence

### B9. Cross-Camera Timeline

Combine Person A events into:

- ordered observations
- first/last seen
- camera sequence
- GIS path

### B10. Camera Health Dashboard

Consume stream/worker health from Person A.

Display:

- online
- reconnecting
- offline
- degraded
- frozen
- dark
- blurred

### B11. RBAC

Implement application-level permissions.

### B12. Audit Logs

Log sensitive actions.

### B13. Deployment

Own:

- docker-compose
- DB/Redis/MinIO
- API/web containers
- environment configuration
- deployment notes

---

# 23. SHARED RESPONSIBILITIES

Both people jointly own:

## S1. Architecture Freeze

Before serious coding:

- finalise module boundaries
- finalise event schema
- finalise DB field names needed by AI
- finalise camera schema

## S2. Integration

Daily integration test:

`live camera → AI event → DB → alert → UI`

Never wait until the end to integrate.

## S3. Government Feed Validation

Test on multiple real sandbox feeds.

## S4. Failure Testing

Test:

- camera reconnect
- H.264/H.265
- mixed resolution
- stream loop/discontinuity
- bad OCR
- duplicate detections
- camera offline

## S5. Scalability Report

Person A:

- GPU/inference requirements

Person B:

- API/database/storage/network architecture

Combine into one report.

## S6. HLD / Architecture Document

Both contribute.

## S7. Submission Presentation

Both contribute.

## S8. Demo Recording

Both validate before submission.

---

# 24. Repository Ownership Structure

Suggested repository:

```text
sentinel-platform/
|
|-- apps/
|   |-- web/                        # Person B
|
|-- services/
|   |-- api/                        # Person B
|   |-- camera-registry/            # Person B
|   |-- event-worker/               # Person B
|   |-- stream-worker/              # Person A
|   |-- ai-inference/               # Person A
|   |-- reid-service/               # Person A
|
|-- models/
|   |-- vehicle-detector/           # Person A
|   |-- plate-detector/             # Person A
|   |-- plate-ocr/                  # Person A
|   |-- vehicle-reid/               # Person A
|
|-- training/
|   |-- vehicle/                    # Person A
|   |-- plate-detection/            # Person A
|   |-- ocr/                        # Person A
|   |-- reid/                       # Person A
|
|-- db/
|   |-- migrations/                 # Person B
|   |-- seeds/                      # Person B
|
|-- infra/
|   |-- docker/                     # Person B
|   |-- gpu/                        # Person A + B
|
|-- docs/
|   |-- architecture/               # Shared
|   |-- ai-models/                  # Person A
|   |-- api/                        # Person B
|   |-- scalability/                # Shared
|   |-- security/                   # Person B
|   |-- submission/                 # Shared
|
|-- ROADMAP.md
```

---

# 25. Integration Boundary Between Person A and Person B

This is critical.

Person A should **not** write frontend/database logic inside the AI service.

Person B should **not** modify AI model code to solve UI issues.

The integration contract should be:

## Person B Sends

Camera configuration:

```json
{
  "camera_id": "CAM-01",
  "rtsp_url": "...",
  "enabled": true
}
```

## Person A Sends

AI event:

```json
{
  "event_type": "ANPR_DETECTION",
  "camera_id": "CAM-01",
  "plate": "...",
  "confidence": 0.94,
  "pts_ms": 123456,
  "evidence": {}
}
```

## Person A Sends

Health event:

```json
{
  "camera_id": "CAM-01",
  "online": true,
  "ai_worker": "healthy",
  "last_pts_ms": 123456
}
```

This boundary lets both people work in parallel.

---

# 26. Development Phases

Because the submission deadline is close, every phase must end in something demonstrable.

---

# PHASE 0 — Architecture Freeze

## Both

Complete before broad coding:

- freeze hybrid model choice
- freeze MVP
- freeze event schema
- freeze database schema v1
- freeze API contract
- choose model families
- create repository
- create branches
- setup issue/task board

Exit condition:

Both people can work independently without guessing interface contracts.

---

# PHASE 1 — Minimum End-to-End Skeleton

## Person A

- read `/api/ingest`
- connect to one RTSP feed
- force RTSP TCP
- read PTS
- reconnect
- run pretrained vehicle detection
- publish dummy/real detection event

## Person B

- FastAPI
- PostgreSQL/PostGIS
- React UI
- camera registry
- ingest catalogue sync
- live HLS viewer
- event endpoint
- basic detection table

## Shared Exit Test

A real Government camera appears in the UI and one AI event reaches the database.

---

# PHASE 2 — ANPR Core

## Person A

- train vehicle model
- train plate model
- fine-tune OCR
- integrate the 3-stage pipeline
- multi-frame OCR consensus
- evidence crops

## Person B

- watchlist CRUD
- alert DB
- live alerts
- vehicle search
- evidence UI

## Shared Exit Test

A plate from a live feed appears in:

- database
- UI
- watchlist comparison

---

# PHASE 3 — Real-Time Police Workflow

## Person A

- run multiple camera workers
- optimise sampling
- deduplicate observations
- improve plate accuracy
- add health signals

## Person B

- command centre
- alert acknowledgment
- camera map
- vehicle timeline
- GIS path
- audit logs
- RBAC

## Shared Exit Test

`camera → plate → watchlist → alert → timeline → GIS`

works end to end.

---

# PHASE 4 — Multi-Camera Intelligence

## Person A

- cross-camera candidate support
- optional ReID
- performance tuning
- batch/worker optimisation

## Person B

- cross-camera correlation engine
- last-seen view
- observed movement map
- confidence presentation

## Shared Exit Test

The same plate detected on 2+ cameras automatically produces one ordered journey.

---

# PHASE 5 — Reliability / Hardening

## Person A

Test:

- H.264
- H.265
- reconnect
- irregular frames
- loop cut
- low-light frames
- OCR failures

## Person B

Test:

- auth
- RBAC
- alert spam
- DB indexes
- duplicate events
- UI refresh
- map load
- evidence permission

## Shared

Run long-duration test.

Document failure cases.

---

# PHASE 6 — Selection-Level Submission Build

Must include:

- working registry
- GIS
- live viewer
- ANPR
- searchable metadata
- watchlist
- real-time alert
- government-feed demo
- multi-camera journey if available
- architecture diagram
- scalability plan
- security design
- output report

At this point, stop adding random features.

---

# PHASE 7 — Winning-Level Bonus Features

Only after the selection build is stable.

Priority order:

1. Vehicle ReID fallback
2. Camera freeze/blur/dark monitoring
3. Better operator workflow
4. Evidence clips
5. Vehicle colour
6. Edge/bandwidth optimisation demonstration
7. Analytics health dashboard
8. Better load-test instrumentation

Do not sacrifice core reliability for these.

---

# 27. Practical Calendar for Two People

## Day 1

Both:

- architecture freeze
- repository
- event contract
- DB schema
- sandbox connection validation

Person A:

- first RTSP capture

Person B:

- registry/API skeleton

## Day 2

Person A:

- pretrained detector live

Person B:

- camera sync + live viewer + GIS base

## Day 3

Person A:

- plate detector integration

Person B:

- watchlist + alert backend

## Day 4

Person A:

- OCR integration

Person B:

- alert UI + investigation UI

## Day 5

Shared:

- first full ANPR end-to-end live test

## Day 6

Person A:

- multi-camera workers + deduplication

Person B:

- timeline + GIS movement

## Day 7

Shared:

- watchlist live demo
- health/reconnect testing

## Day 8

Person A:

- model accuracy/performance tuning

Person B:

- RBAC + audit + dashboard polishing

## Day 9

Shared:

- long live test
- fix critical failures

## Day 10

Shared:

- HLD
- architecture
- load/scalability report
- security document

## Day 11

Shared:

- own-feed demo
- Government-feed demo
- output report
- screenshots

## Day 12

Shared:

- presentation
- final regression test
- submission links
- credentials
- backup deployment

The exact dates can be shifted, but do not move integration to the final days.

---

# 28. Model Training Order

The correct order is:

## Training Job 1

**Vehicle Detector**

Purpose:

reliable vehicle regions.

## Training Job 2

**Plate Detector**

Purpose:

high recall on plates.

## Training Job 3

**Plate OCR**

Purpose:

high full-string recognition accuracy.

## Integration Milestone

Before training anything else:

run:

`live feed → vehicle → plate → OCR`

## Training Job 4

**Vehicle ReID**

Only after ANPR works.

## Training Job 5

**Vehicle Attributes**

Only if time remains.

---

# 29. Kaggle Training Workflow

For each trainable model:

1. Verify dataset licence.
2. Download/attach dataset.
3. Inspect annotation quality manually.
4. Remove corrupted samples.
5. Ensure no near-duplicate leakage between train/validation/test.
6. Create fixed train/val/test split.
7. Train from pretrained weights instead of from scratch unless there is a strong reason.
8. Save:
   - best weights
   - last weights
   - config
   - class mapping
   - metrics
   - confusion matrix
   - sample predictions
9. Export preferred runtime format:
   - PyTorch first
   - ONNX next
   - TensorRT only after the pipeline is stable
10. Version every model.

Example naming:

```text
vehicle_detector_v1.pt
plate_detector_v1.pt
plate_ocr_v1/
vehicle_reid_v1.pth
```

Never overwrite a known-good model.

---

# 30. Model Version Registry

Maintain a simple table:

| Model | Version | Dataset | Input | Metric | Runtime | Status |
|---|---|---|---|---|---|---|
| Vehicle | v1 | ... | 640 | ... | PyTorch | baseline |
| Plate | v1 | ... | 640 | ... | PyTorch | active |
| OCR | v1 | ... | crop | ... | Paddle | active |
| ReID | v1 | ... | 256 | ... | PyTorch | optional |

This helps during evaluation and documentation.

---

# 31. End-to-End ANPR Quality Is More Important Than Individual Model Accuracy

Do not optimise only mAP.

The important test is:

```text
raw CCTV frame
      |
      v
vehicle found?
      |
      v
plate found?
      |
      v
plate read correctly?
      |
      v
watchlist matched?
```

Measure:

**Full pipeline exact plate success rate.**

A great OCR model is useless if the plate detector misses the crop.

---

# 32. False-Alert Control

Critical policing systems must avoid alert spam.

Rules:

- minimum plate confidence
- exact match for critical alert
- deduplicate same camera/vehicle event
- combine multiple OCR frames
- retain raw evidence
- allow operator verification
- mark uncertain matches as `POSSIBLE`, not `CONFIRMED`

---

# 33. Observability

Log:

- stream connection
- reconnect attempts
- decoder errors
- inference latency
- model errors
- event creation
- queue lag
- DB latency
- alert latency
- WebSocket status

Metrics dashboard can show:

- cameras connected
- cameras processed by AI
- detections/min
- ANPR events/min
- average AI latency
- queue depth
- alert latency

---

# 34. Acceptance Tests

The build is not ready until these work.

## Camera

- dynamic discovery works
- live status works
- no hard-coded IDs
- RTSP reconnect works

## AI

- vehicle detected
- plate detected
- OCR produced
- confidence stored

## Metadata

- camera
- location
- PTS/time
- plate
- evidence

are persisted.

## Watchlist

- test plate can be added
- match is detected automatically
- alert appears

## Search

- exact plate search returns history

## Multi-Camera

- 2+ observations produce ordered timeline

## GIS

- cameras visible
- journey visible

## Security

- unauthorised user cannot modify watchlist
- actions are audited

---

# 35. Must-Have Selection Features

Do not submit without:

- dynamic Government camera onboarding
- Government live feed viewing
- vehicle detection
- number-plate detection
- OCR/ANPR
- watchlist database
- automatic real-time alert
- searchable detection history
- camera/time/location metadata
- GIS camera map
- working backend
- architecture document
- scale strategy

---

# 36. Winning-Level Features

Strong additional value:

- robust multi-camera correlation
- vehicle journey
- vehicle ReID fallback
- event evidence
- camera health/tamper
- RBAC
- auditability
- dynamic connector architecture
- low-bandwidth strategy
- measured load/performance report
- polished operator workflow

---

# 37. Features to Avoid Before Core Completion

Do not distract the team with:

- chatbot
- LLM assistant
- predictive policing
- emotion detection
- dozens of AI classes
- face recognition
- drone integration
- mobile app
- blockchain
- complex microservices for every tiny feature
- Kubernetes during MVP
- full video archival infrastructure

These can be future-roadmap items.

---

# 38. Submission Documents Checklist

Prepare:

## Solution Presentation

Include:

- problem understanding
- selected hybrid model
- architecture
- workflow
- AI models
- innovation
- Government-feed evidence
- security
- scalability
- operational benefit

## High-Level Design

Include:

- components
- APIs
- stream flow
- data flow
- event schema
- DB
- AI pipeline
- deployment
- security
- failure handling
- scale architecture

## Own-Feed Demo

2–3 minutes maximum if following current official guidance.

Show:

- feed onboarding
- AI
- ANPR
- watchlist
- alert

## Government Feed Demo

Show:

- real Sentinel feed
- AI output
- detected plate
- timestamp
- report

## Output Report

Include:

- camera
- time
- plate
- confidence
- image/evidence
- processing latency where useful

## Scalability Report

Include:

- compute
- GPU
- network
- storage
- regional architecture
- HA
- DR
- cost assumptions

## Security Document

Include:

- authentication
- RBAC
- encryption
- segmentation
- audit
- secrets
- backups
- DR

---

# 39. Final Success Definition

The project succeeds when this live sequence works reliably:

```text
Official Sentinel Camera
          |
          v
Vehicle Detected
          |
          v
Licence Plate Detected
          |
          v
Plate Read
          |
          v
Camera + Time + Location Saved
          |
          v
Watchlist Checked Automatically
          |
       MATCH
          |
          v
Real-Time Alert
          |
          v
Evidence Available
          |
          v
Same Vehicle Seen Elsewhere
          |
          v
Cross-Camera Timeline
          |
          v
GIS Observed Movement Path
          |
          v
Police Investigation View
```

This is the central project promise.

---

# 40. Final Priority Order

If time becomes limited, work in this exact order:

1. Live stream reliability
2. Vehicle detector
3. Plate detector
4. OCR
5. Event persistence
6. Watchlist
7. Real-time alert
8. Camera registry
9. GIS
10. Vehicle search
11. Multi-camera timeline
12. Camera health
13. RBAC/audit
14. Vehicle ReID
15. Cosmetic UI improvements
16. Other analytics

A beautiful dashboard with unreliable ANPR is weaker than a simple dashboard with a reliable live detection pipeline.

---

# 41. Official Reference Pages

- Gujarat Police Innovation Hackathon 2026 — Problem Statement & Solution Flow  
  https://sentinel.gujarat.gov.in/problems

- Sentinel Sandbox — Camera Integration Guide  
  https://sentinel.gujarat.gov.in/resource

Use the live official site as the source of truth because camera availability, IDs and instructions can change.

---

# 42. Team Rule

Every day, both people must prove the current build with the same end-to-end test:

> **Can a real Sentinel camera produce an AI detection that reaches the operator UI?**

If the answer is no, fix that before adding a new feature.

