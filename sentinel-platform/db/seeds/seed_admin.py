"""
Seed script — creates the default super_admin user.
Run once after docker-compose up (DB must be running):
  python db/seeds/seed_admin.py
"""
import asyncio
import sys
import os

# Override DATABASE_URL to use localhost (seed runs outside Docker)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://sentinel:sentinel_secret@localhost:5433/sentinel_db")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'api'))

from app.core.database import AsyncSessionLocal, engine, Base
from app.models.user import User
from app.auth.security import get_password_hash
from sqlalchemy import select, text


async def main():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == "admin@sentinel.gujarat.gov.in"))
        if existing.scalar_one_or_none():
            print("Admin user already exists.")
            return

        admin = User(
            email="admin@sentinel.gujarat.gov.in",
            full_name="Sentinel Administrator",
            password_hash=get_password_hash("Sentinel@2026"),
            role="super_admin",
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print("✅ Admin user created:")
        print("   Email:    admin@sentinel.gujarat.gov.in")
        print("   Password: Sentinel@2026")
        print("   Role:     super_admin")
        print("\n⚠️  CHANGE THE PASSWORD AFTER FIRST LOGIN!")


if __name__ == "__main__":
    asyncio.run(main())
