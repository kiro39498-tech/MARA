"""
Local development seed script.
Creates first admin user if database is empty.

Usage:
    cd backend
    source .venv/bin/activate
    python -m scripts.seed_admin
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select  # noqa: E402
from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.user import User, Role  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.services.user_service import UserService  # noqa: E402
from app.schemas.user import UserCreate  # noqa: E402


async def main():
    """Create admin user if no users exist."""
    async with AsyncSessionLocal() as db:
        # Check if any users exist
        result = await db.execute(select(User).limit(1))
        existing_user = result.scalars().first()

        if existing_user:
            print("[WARNING] Users already exist in database. Seeding skipped.")
            print(
                "   Existing user:"
                f" {existing_user.username} ({existing_user.email})"
            )
            return

        # Create admin user directly using the SQLAlchemy model to bypass UserCreate constraints (e.g. password uppercase policy)
        try:
            # Get ADMIN role
            role_result = await db.execute(select(Role).filter(Role.name == "ADMIN"))
            admin_role = role_result.scalar_one_or_none()
            if not admin_role:
                admin_role = Role(name="ADMIN", description="Full system access")
                db.add(admin_role)
                await db.flush()

            from app.core.security import get_password_hash
            hashed_password = get_password_hash(settings.FIRST_SUPERUSER_PASSWORD)

            user = User(
                email=settings.FIRST_SUPERUSER_EMAIL,
                username="admin",
                full_name="Admin User",
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=True,
                roles=[admin_role],
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)

            print("[OK] Admin user created successfully!")
            print(f"   Email:    {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Password: {settings.FIRST_SUPERUSER_PASSWORD}")
            print("\n[INFO] Test login:")
            print(
                "   curl -X POST"
                " 'http://127.0.0.1:8000/api/v1/auth/login' \\"
            )
            print(
                "     -H"
                " 'Content-Type: application/x-www-form-urlencoded' \\"
            )
            print(
                "     -d 'username=admin&password="
                f"{settings.FIRST_SUPERUSER_PASSWORD}'"
            )

        except Exception as e:
            print(f"[ERROR] Error creating admin user: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
