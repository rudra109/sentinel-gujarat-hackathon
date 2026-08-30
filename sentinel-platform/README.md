# Sentinel Unified Intelligence Platform
### Person B — Platform / Backend / Frontend / GIS

> **Hackathon:** Gujarat Police Innovation Hackathon 2026  
> **Owner:** Person B  
> **Person A Integration:** Consumes AI events from Redis Streams (no model code here)

---

## Quick Start

### 1. Copy environment file
```bash
cp .env.example .env
# Edit .env — set SENTINEL_INGEST_URL and credentials
```

### 2. Start all services
```bash
cd infra/docker
docker-compose up -d
```

### 3. Seed the admin user
```bash
# From sentinel-platform/
python db/seeds/seed_admin.py
```
Default credentials:
- **Email:** `admin@sentinel.gujarat.gov.in`  
- **Password:** `Sentinel@2026`
- ⚠️ Change password after first login!

### 4. Start frontend (dev)
```bash
cd apps/web
npm install
npm run dev
# Open http://localhost:5173
```

### 5. Access the API docs
```
http://localhost:8000/docs
```

---

## Architecture

```
sentinel-platform/
├── apps/
│   └── web/                   # React + Vite frontend (10 screens)
├── services/
│   ├── api/                   # FastAPI backend
│   │   └── app/
│   │       ├── main.py        # App entry + lifespan
│   │       ├── routers/       # auth, cameras, watchlist, alerts, detections, investigation, health, audit
│   │       ├── models/        # SQLAlchemy ORM models
│   │       ├── schemas/       # Pydantic schemas
│   │       ├── services/      # event_processor.py (dedup + watchlist match + alert)
│   │       ├── auth/          # JWT + RBAC
│   │       ├── core/          # config, database, redis_client
│   │       └── utils/         # ws_manager, audit log helper
│   └── event-worker/          # Redis Stream consumer (processes Person A events)
├── db/
│   └── seeds/                 # seed_admin.py
├── infra/
│   └── docker/                # docker-compose.yml
└── .env.example
```

---

## Integration Contract with Person A

### Person A → Person B (AI detection event via Redis Stream `sentinel:ai:events`)
```json
{
  "event_type": "ANPR_DETECTION",
  "camera_id": "CAM-01",
  "pts_ms": 123456,
  "observed_at": "ISO timestamp",
  "vehicle": { "type": "car", "confidence": 0.94, "track_id": 181 },
  "plate": { "raw": "GJO5ABI234", "normalised": "GJ05AB1234", "confidence": 0.91 },
  "evidence": { "snapshot": "path/url", "plate_crop": "path/url" }
}
```

### Person A → Person B (Health event via Redis Stream `sentinel:health:events`)
```json
{
  "camera_id": "CAM-01",
  "online": true,
  "ai_worker": "healthy",
  "last_pts_ms": 123456
}
```

### Person B → Person A (Camera config via `GET /cameras/ai-config/all`)
```json
[{ "camera_id": "CAM-01", "rtsp_url": "...", "enabled": true }]
```

---

## RBAC Roles

| Role | Capabilities |
|---|---|
| `super_admin` | Full access, user management, audit |
| `state_operator` | All cameras, alerts, investigations, watchlist |
| `district_operator` | Assigned district cameras |
| `department_operator` | Assigned department cameras |
| `investigator` | Search, evidence, journey, alerts |
| `viewer` | Read-only access |

---

## Frontend Screens

| # | Screen | URL |
|---|---|---|
| 1 | Command Centre | `/` |
| 2 | Camera Registry | `/cameras` |
| 3 | GIS Camera Map | `/gis` |
| 4 | Live Control Room | `/live` |
| 5 | Watchlist | `/watchlist` |
| 6 | Alerts | `/alerts` |
| 7 | Vehicle Investigation | `/investigation` |
| 8 | Vehicle Journey | `/journey/:plate` |
| 9 | Camera Health | `/health` |
| 10 | Audit Logs | `/audit` |

---

## Key Features

- **Dynamic camera sync** from Sentinel `/api/ingest` (every 60s + on demand)
- **Deduplication:** same camera + track + plate within 30s = one observation
- **Watchlist matching:** exact match → `CRITICAL/HIGH`, Levenshtein distance 1 → `POSSIBLE/MEDIUM`
- **Real-time alerts** via WebSocket pushed to all operator browsers
- **GIS movement path** for cross-camera vehicle journey
- **HLS.js** live streaming in multi-camera grid (4/9/16)
- **Full RBAC** with route-level permission enforcement
- **Complete audit trail** for all sensitive actions
- **Toast notifications** pop up on every watchlist match

---

## Person A `.pt` Files

> **This repository does NOT contain any model training code.**  
> When Person A provides the `.pt` files (vehicle detector, plate detector, OCR), they integrate them into `services/ai-inference/` (their ownership).  
> This platform receives the output events from their pipeline.
