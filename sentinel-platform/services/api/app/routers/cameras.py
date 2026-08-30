"""
Camera Registry Router (B3)
- CRUD for cameras
- Dynamic sync from Sentinel /api/ingest
- CSV bulk import endpoint
- Camera config endpoint for Person A's AI workers
"""
import csv
import io
import httpx
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from geoalchemy2.functions import ST_SetSRID, ST_MakePoint

from app.core.database import get_db
from app.core.config import settings
from app.models.camera import Camera, CameraStatus
from app.models.user import User
from app.schemas.camera import CameraCreate, CameraUpdate, CameraOut, CameraConfigForAI
from app.auth.security import get_current_user, REQUIRE_OPERATOR_UP
from app.utils.audit import audit_log

router = APIRouter(prefix="/cameras", tags=["Camera Registry"])


@router.get("", response_model=List[CameraOut])
async def list_cameras(
    district: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(200, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Camera)
    if district:
        q = q.where(Camera.district == district)
    if department:
        q = q.where(Camera.department == department)
    if status:
        q = q.where(Camera.live_status == status)
    if search:
        q = q.where(Camera.name.ilike(f"%{search}%"))
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    return [CameraOut.model_validate(c) for c in result.scalars().all()]


@router.get("/stats")
async def camera_stats(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    total = await db.scalar(select(func.count(Camera.id)))
    online = await db.scalar(select(func.count(Camera.id)).where(Camera.live_status == CameraStatus.online))
    offline = await db.scalar(select(func.count(Camera.id)).where(Camera.live_status == CameraStatus.offline))
    ai_active = await db.scalar(select(func.count(Camera.id)).where(Camera.ai_enabled == True))
    return {"total": total, "online": online, "offline": offline, "ai_active": ai_active}


@router.get("/{camera_id}", response_model=CameraOut)
async def get_camera(camera_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    cam = await db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return CameraOut.model_validate(cam)


@router.post("", response_model=CameraOut, dependencies=[REQUIRE_OPERATOR_UP])
async def create_camera(payload: CameraCreate, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    cam = Camera(**payload.model_dump())
    if payload.latitude and payload.longitude:
        cam.location = ST_SetSRID(ST_MakePoint(payload.longitude, payload.latitude), 4326)
    db.add(cam)
    await db.commit()
    await db.refresh(cam)
    await audit_log(db, "CAMERA_CREATED", user_id=current_user.id, entity_type="camera", entity_id=str(cam.id))
    return CameraOut.model_validate(cam)


@router.patch("/{camera_id}", response_model=CameraOut, dependencies=[REQUIRE_OPERATOR_UP])
async def update_camera(camera_id: int, payload: CameraUpdate, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    cam = await db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(cam, k, v)
    if payload.latitude and payload.longitude:
        cam.location = ST_SetSRID(ST_MakePoint(payload.longitude, payload.latitude), 4326)
    await db.commit()
    await db.refresh(cam)
    await audit_log(db, "CAMERA_UPDATED", user_id=current_user.id, entity_type="camera", entity_id=str(camera_id))
    return CameraOut.model_validate(cam)


@router.post("/sync", summary="Sync cameras from Sentinel /api/ingest")
async def sync_cameras(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    """Trigger a manual camera catalogue sync."""
    background_tasks.add_task(_sync_from_ingest, db)
    await audit_log(db, "CAMERA_SYNC_TRIGGERED", user_id=current_user.id)
    return {"message": "Camera sync triggered"}


async def _sync_from_ingest(db: AsyncSession):
    """Fetch cameras from Sentinel sandbox and upsert into DB."""
    headers = {}
    if settings.SENTINEL_API_KEY:
        headers["Authorization"] = f"Bearer {settings.SENTINEL_API_KEY}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(settings.SENTINEL_INGEST_URL, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return  # Graceful — logged externally

    cameras = data if isinstance(data, list) else data.get("cameras", [])
    for cam_data in cameras:
        ext_id = str(cam_data.get("id") or cam_data.get("camera_id", ""))
        if not ext_id:
            continue
        existing = await db.execute(select(Camera).where(Camera.external_camera_id == ext_id))
        cam = existing.scalar_one_or_none()
        if cam is None:
            cam = Camera(external_camera_id=ext_id)
            db.add(cam)
        cam.name = cam_data.get("name", ext_id)
        cam.rtsp_url = cam_data.get("rtsp_url") or cam_data.get("rtsp")
        cam.hls_url = cam_data.get("hls_url") or cam_data.get("hls")
        cam.webrtc_url = cam_data.get("webrtc_url") or cam_data.get("webrtc")
        cam.latitude = cam_data.get("latitude") or cam_data.get("lat")
        cam.longitude = cam_data.get("longitude") or cam_data.get("lon")
        cam.department = cam_data.get("department")
        cam.district = cam_data.get("district")
    await db.commit()


@router.post("/bulk-import", summary="Bulk import cameras from CSV")
async def bulk_import(file: UploadFile = File(...), db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    count = 0
    for row in reader:
        ext_id = row.get("external_camera_id") or row.get("id", "")
        if not ext_id:
            continue
        existing = await db.execute(select(Camera).where(Camera.external_camera_id == ext_id))
        cam = existing.scalar_one_or_none()
        if cam is None:
            cam = Camera(external_camera_id=ext_id)
            db.add(cam)
        cam.name = row.get("name", ext_id)
        cam.rtsp_url = row.get("rtsp_url")
        cam.hls_url = row.get("hls_url")
        cam.latitude = float(row["latitude"]) if row.get("latitude") else None
        cam.longitude = float(row["longitude"]) if row.get("longitude") else None
        cam.district = row.get("district")
        cam.department = row.get("department")
        count += 1
    await db.commit()
    await audit_log(db, "CAMERA_BULK_IMPORT", user_id=current_user.id, metadata={"count": count})
    return {"imported": count}


@router.get("/ai-config/all", response_model=List[CameraConfigForAI])
async def get_ai_config(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    """Returns camera RTSP config for Person A's AI workers."""
    result = await db.execute(select(Camera).where(Camera.rtsp_url.isnot(None)))
    cams = result.scalars().all()
    return [
        CameraConfigForAI(
            camera_id=c.external_camera_id,
            rtsp_url=c.rtsp_url,
            enabled=c.ai_enabled,
        )
        for c in cams
    ]
