"""
Alerts Router (B7)
- List alerts (with filters)
- Get single alert detail with evidence
- Acknowledge alert
- WebSocket endpoint for real-time alert push
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.core.database import get_db
from app.models.detection import Alert, VehicleObservation, Evidence
from app.models.user import User
from app.schemas.detection import AlertOut, AlertAcknowledge
from app.auth.security import get_current_user
from app.utils.ws_manager import manager
from app.utils.audit import audit_log

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.websocket("/ws")
async def alerts_websocket(websocket: WebSocket):
    """Real-time alert WebSocket — connect and receive live alert pushes."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; client sends pings
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.get("", response_model=List[AlertOut])
async def list_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    camera_id: Optional[str] = Query(None),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Alert)
    if status:
        q = q.where(Alert.status == status)
    if severity:
        q = q.where(Alert.severity == severity)
    if camera_id:
        q = q.where(Alert.camera_id == camera_id)
    if start:
        q = q.where(Alert.created_at >= start)
    if end:
        q = q.where(Alert.created_at <= end)
    q = q.order_by(Alert.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return [AlertOut.model_validate(a) for a in result.scalars().all()]


@router.get("/stats")
async def alert_stats(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    total = await db.scalar(select(func.count(Alert.id)))
    open_count = await db.scalar(select(func.count(Alert.id)).where(Alert.status == "OPEN"))
    critical = await db.scalar(select(func.count(Alert.id)).where(
        Alert.status == "OPEN", Alert.severity == "CRITICAL"
    ))
    return {"total": total, "open": open_count, "critical": critical}


@router.get("/{alert_id}", response_model=AlertOut)
async def get_alert(alert_id: int, db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await audit_log(db, "ALERT_VIEWED", user_id=current_user.id, entity_type="alert", entity_id=str(alert_id))
    return AlertOut.model_validate(alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
async def acknowledge_alert(
    alert_id: int,
    payload: AlertAcknowledge,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.status != "OPEN":
        raise HTTPException(status_code=400, detail="Alert already acknowledged")
    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.now(timezone.utc)
    alert.notes = payload.notes
    await db.commit()
    await db.refresh(alert)
    await audit_log(
        db, "ALERT_ACKNOWLEDGED", user_id=current_user.id,
        entity_type="alert", entity_id=str(alert_id),
        metadata={"notes": payload.notes},
    )
    return AlertOut.model_validate(alert)
