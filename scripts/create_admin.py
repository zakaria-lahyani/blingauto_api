#!/usr/bin/env python3
"""
Create default admin user on application startup.

This script creates an initial admin user if one doesn't exist.
It's designed to be run during Docker container initialization.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.core.config.settings import settings
from app.features.auth.domain.entities import User, UserRole, UserStatus
from app.features.auth.adapters.models import UserModel
from app.features.auth.adapters.services import PasswordHasher


async def create_admin_user(
    email: str,
    password: str,
    first_name: str = "Admin",
    last_name: str = "User"
):
    """
    Create default admin user if it doesn't exist.

    Args:
        email: Admin email address
        password: Admin password (will be hashed)
        first_name: Admin first name
        last_name: Admin last name
    """
    print("=" * 80)
    print("Creating Default Admin User")
    print("=" * 80)

    # Create async engine
    engine = create_async_engine(
        settings.database_url,
        echo=False,
    )

    # Create async session factory
    async_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with async_session_factory() as session:
            # Check if admin already exists
            from sqlalchemy import select
            stmt = select(UserModel).where(UserModel.email == email.lower())
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"✓ Admin user already exists: {email}")
                print(f"  User ID: {existing_user.id}")
                print(f"  Role: {existing_user.role}")
                print(f"  Status: {existing_user.status}")
                return True

            # Create new admin user
            print(f"\nCreating new admin user: {email}")

            # Hash password
            password_hasher = PasswordHasher()
            hashed_password = password_hasher.hash(password)

            # Create user entity
            admin_user = User.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                hashed_password=hashed_password,
                role=UserRole.ADMIN,
            )

            # Override status to ACTIVE and email_verified for admin
            admin_user.status = UserStatus.ACTIVE
            admin_user.email_verified = True
            admin_user.email_verified_at = datetime.utcnow()

            # Convert to database model
            admin_model = UserModel(
                id=admin_user.id,
                email=admin_user.email,
                first_name=admin_user.first_name,
                last_name=admin_user.last_name,
                hashed_password=admin_user.hashed_password,
                role=admin_user.role.value,
                status=admin_user.status.value,
                phone_number=admin_user.phone_number,
                email_verified=admin_user.email_verified,
                email_verified_at=admin_user.email_verified_at,
                last_login_at=admin_user.last_login_at,
                failed_login_attempts=admin_user.failed_login_attempts,
                locked_until=admin_user.locked_until,
                password_changed_at=admin_user.password_changed_at,
                created_at=admin_user.created_at,
                updated_at=admin_user.updated_at,
            )

            # Save to database
            session.add(admin_model)
            await session.commit()
            await session.refresh(admin_model)

            print(f"\n✓ Admin user created successfully!")
            print(f"  User ID: {admin_model.id}")
            print(f"  Email: {admin_model.email}")
            print(f"  Name: {admin_model.first_name} {admin_model.last_name}")
            print(f"  Role: {admin_model.role}")
            print(f"  Status: {admin_model.status}")
            print(f"  Email Verified: {admin_model.email_verified}")
            print(f"\n⚠️  IMPORTANT: Change the admin password after first login!")

            return True

    except Exception as e:
        print(f"\n✗ Error creating admin user: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


async def main():
    """Main function to create admin user from environment variables."""
    # Get admin credentials from environment
    admin_email = os.getenv("INITIAL_ADMIN_EMAIL")
    admin_password = os.getenv("INITIAL_ADMIN_PASSWORD")
    admin_first_name = os.getenv("INITIAL_ADMIN_FIRST_NAME", "Admin")
    admin_last_name = os.getenv("INITIAL_ADMIN_LAST_NAME", "User")

    if not admin_email or not admin_password:
        print("\n⚠️  Admin credentials not configured")
        print("   Set INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_PASSWORD environment variables")
        print("   to create a default admin user on startup.\n")
        return True  # Not an error, just not configured

    print(f"\nAdmin Configuration:")
    print(f"  Email: {admin_email}")
    print(f"  First Name: {admin_first_name}")
    print(f"  Last Name: {admin_last_name}")
    print(f"  Password: {'*' * len(admin_password)}")
    print()

    success = await create_admin_user(
        email=admin_email,
        password=admin_password,
        first_name=admin_first_name,
        last_name=admin_last_name,
    )

    if success:
        print("\n" + "=" * 80)
        print("Admin User Setup Complete")
        print("=" * 80 + "\n")
        return True
    else:
        print("\n" + "=" * 80)
        print("Admin User Setup Failed")
        print("=" * 80 + "\n")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
