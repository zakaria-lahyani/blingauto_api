#!/usr/bin/env python3
"""
Create default admin user on deployment - Simplified version.

This script creates an initial admin user using direct SQL to avoid
circular import issues with SQLAlchemy relationships.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.core.config.settings import settings
from app.core.security import password_hasher


async def create_admin_user(
    email: str,
    password: str,
    first_name: str = "Admin",
    last_name: str = "User"
):
    """
    Create default admin user using direct SQL to avoid circular imports.

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
            check_query = text("SELECT id, email, role, is_active FROM users WHERE email = :email")
            result = await session.execute(check_query, {"email": email.lower()})
            existing_user = result.fetchone()

            if existing_user:
                print(f"✓ Admin user already exists: {email}")
                print(f"  User ID: {existing_user[0]}")
                print(f"  Role: {existing_user[2]}")
                print(f"  Active: {existing_user[3]}")
                return True

            # Create new admin user using raw SQL
            print(f"\nCreating new admin user: {email}")

            # Hash password
            hashed_password = password_hasher.hash(password)

            # Generate UUID
            user_id = str(uuid.uuid4())
            now = datetime.utcnow()

            # Insert user with raw SQL
            insert_query = text("""
                INSERT INTO users (
                    id, email, first_name, last_name, password_hash,
                    role, is_active, is_email_verified, email_verified_at,
                    failed_login_attempts, created_at, updated_at
                ) VALUES (
                    :id, :email, :first_name, :last_name, :password_hash,
                    :role, :is_active, :is_email_verified, :email_verified_at,
                    :failed_login_attempts, :created_at, :updated_at
                )
            """)

            await session.execute(insert_query, {
                "id": user_id,
                "email": email.lower(),
                "first_name": first_name,
                "last_name": last_name,
                "password_hash": hashed_password,
                "role": "admin",
                "is_active": True,
                "is_email_verified": True,
                "email_verified_at": now,
                "failed_login_attempts": 0,
                "created_at": now,
                "updated_at": now,
            })

            await session.commit()

            print(f"\n✓ Admin user created successfully!")
            print(f"  User ID: {user_id}")
            print(f"  Email: {email}")
            print(f"  Name: {first_name} {last_name}")
            print(f"  Role: admin")
            print(f"  Active: True")
            print(f"  Email Verified: True")
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
