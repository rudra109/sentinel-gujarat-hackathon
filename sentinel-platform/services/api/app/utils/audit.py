"""
Audit log utility.
Call audit_log() from any route to persist sensitive actions.
"""
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.detection import AuditLog


async def audit_log(
    db: AsyncSession,
    action: str,
    user_id: int | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    metadata: dict | None = None,
    ip_address: str | None = None,
):
    """Persist an audit log entry."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        metadata=json.dumps(metadata) if metadata else None,
        ip_address=ip_address,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.commit()
