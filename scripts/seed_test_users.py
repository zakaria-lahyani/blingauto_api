#!/usr/bin/env python3
"""
Seed test users for Postman tests.
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


async def create_test_user(
    session: AsyncSession,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str
):
    """Create a test user."""

    # Check if user already exists
    check_query = text("SELECT id, email, role FROM users WHERE email = :email")
    result = await session.execute(check_query, {"email": email.lower()})
    existing_user = result.fetchone()

    if existing_user:
        print(f"  ✓ User already exists: {email} (role: {existing_user[2]})")
        return True

    # Hash password
    hashed_password = password_hasher.hash(password)

    # Generate UUID
    user_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Insert user
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
        "role": role,
        "is_active": True,
        "is_email_verified": True,
        "email_verified_at": now,
        "failed_login_attempts": 0,
        "created_at": now,
        "updated_at": now,
    })

    print(f"  ✓ Created: {email} (role: {role})")
    return True


async def main():
    """Main function to seed test users."""
    print("=" * 80)
    print("Seeding Test Users for Postman")
    print("=" * 80)
    print()

    # Create async engine
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with async_session_factory() as session:
            # Test users configuration
            test_users = [
                {
                    "email": "client@blingauto.com",
                    "password": "ClientPass123!",
                    "first_name": "Test",
                    "last_name": "Client",
                    "role": "client"
                },
                {
                    "email": "client.manager@blingauto.com",
                    "password": "ClientPass123!",
                    "first_name": "Test",
                    "last_name": "Client",
                    "role": "client"
                },
                {
                    "email": "client.admin@blingauto.com",
                    "password": "ClientPass123!",
                    "first_name": "Test",
                    "last_name": "Client",
                    "role": "client"
                },
                {
                    "email": "client.washer@blingauto.com",
                    "password": "ClientPass123!",
                    "first_name": "Test",
                    "last_name": "Client",
                    "role": "client"
                },
                {
                    "email": "manager@blingauto.com",
                    "password": "ManagerPass123!",
                    "first_name": "Test",
                    "last_name": "Manager",
                    "role": "manager"
                },
                {
                    "email": "washer@blingauto.com",
                    "password": "WasherPass123!",
                    "first_name": "Test",
                    "last_name": "Washer",
                    "role": "washer"
                },
            ]

            for user_data in test_users:
                await create_test_user(session, **user_data)

            await session.commit()

            print()
            print("=" * 80)
            print("✓ Test Users Seeded Successfully")
            print("=" * 80)
            print()
            print("Available test accounts:")
            for user in test_users:
                print(f"  • {user['role'].upper()}: {user['email']} / {user['password']}")
            print()

            return True

    except Exception as e:
        print(f"\n✗ Error seeding test users: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
