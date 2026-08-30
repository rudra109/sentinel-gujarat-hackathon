from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserOut
from app.auth.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, REQUIRE_ADMIN,
)
from app.utils.audit import audit_log

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")

    # Update last login
    await db.execute(
        update(User).where(User.id == user.id).values(last_login_at=datetime.now(timezone.utc))
    )
    await db.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role})
    await audit_log(db, "LOGIN", user_id=user.id, ip_address=request.client.host if request.client else None)

    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.post("/users", response_model=UserOut, dependencies=[REQUIRE_ADMIN])
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        district=payload.district,
        department=payload.department,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await audit_log(db, "USER_CREATED", user_id=current_user.id, entity_type="user", entity_id=str(user.id))
    return UserOut.model_validate(user)
