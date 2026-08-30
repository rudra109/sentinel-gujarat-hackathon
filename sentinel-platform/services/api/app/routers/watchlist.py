"""
Watchlist Engine Router (B6)
- CRUD for watchlist entries
- Search / filter
- Exact + near-match logic lives in the event worker; here we expose management API
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.models.detection import Watchlist
from app.models.user import User
from app.schemas.detection import WatchlistCreate, WatchlistOut
from app.auth.security import get_current_user, REQUIRE_OPERATOR_UP
from app.utils.audit import audit_log

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


@router.get("", response_model=List[WatchlistOut])
async def list_watchlist(
    active_only: bool = Query(True),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Watchlist)
    if active_only:
        q = q.where(Watchlist.active == 1)
    if category:
        q = q.where(Watchlist.category == category)
    if search:
        q = q.where(Watchlist.plate_number.ilike(f"%{search}%"))
    result = await db.execute(q.order_by(Watchlist.priority, Watchlist.created_at.desc()))
    return [WatchlistOut.model_validate(w) for w in result.scalars().all()]


@router.post("", response_model=WatchlistOut, dependencies=[REQUIRE_OPERATOR_UP])
async def add_to_watchlist(
    payload: WatchlistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    normalised = payload.plate_number.upper().replace(" ", "").replace("-", "")
    entry = Watchlist(
        plate_number=normalised,
        category=payload.category,
        priority=payload.priority,
        reason=payload.reason,
        expires_at=payload.expires_at,
        created_by=current_user.id,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    await audit_log(
        db, "WATCHLIST_ADDED", user_id=current_user.id,
        entity_type="watchlist", entity_id=str(entry.id),
        metadata={"plate": normalised, "category": payload.category},
    )
    return WatchlistOut.model_validate(entry)


@router.delete("/{watchlist_id}", dependencies=[REQUIRE_OPERATOR_UP])
async def remove_from_watchlist(
    watchlist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = await db.get(Watchlist, watchlist_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    entry.active = 0
    await db.commit()
    await audit_log(
        db, "WATCHLIST_REMOVED", user_id=current_user.id,
        entity_type="watchlist", entity_id=str(watchlist_id),
        metadata={"plate": entry.plate_number},
    )
    return {"message": "Deactivated"}


@router.get("/{watchlist_id}", response_model=WatchlistOut)
async def get_watchlist_entry(watchlist_id: int, db: AsyncSession = Depends(get_db),
                               _: User = Depends(get_current_user)):
    entry = await db.get(Watchlist, watchlist_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    return WatchlistOut.model_validate(entry)
