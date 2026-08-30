"""
Audit Logs Router (B12)
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.detection import AuditLog
from app.models.user import User
from app.schemas.detection import AuditLogOut
from app.auth.security import get_current_user, REQUIRE_ADMIN

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogOut], dependencies=[REQUIRE_ADMIN])
async def list_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(AuditLog)
    if user_id:
        q = q.where(AuditLog.user_id == user_id)
    if action:
        q = q.where(AuditLog.action.ilike(f"%{action}%"))
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
    if start:
        q = q.where(AuditLog.timestamp >= start)
    if end:
        q = q.where(AuditLog.timestamp <= end)
    q = q.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return [AuditLogOut.model_validate(a) for a in result.scalars().all()]
