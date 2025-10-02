#!/usr/bin/env python
"""Update admin password directly in database."""

import asyncio
import os
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

# Create password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get database URL
database_url = os.getenv("DATABASE_URL", "postgresql://blingauto_user:blingauto_pass@localhost:5432/blingauto").replace("+asyncpg", "")

# Hash the password
password_hash = pwd_context.hash("password123")
print(f"Generated hash: {password_hash}")

# Update the database
engine = create_engine(database_url)

with engine.connect() as conn:
    conn.execute(
        text("UPDATE users SET password_hash = :hash WHERE email = :email"),
        {"hash": password_hash, "email": "admin@blingauto.com"}
    )
    conn.commit()
    print("Password updated successfully!")

# Verify
with engine.connect() as conn:
    result = conn.execute(
        text("SELECT email, password_hash FROM users WHERE email = :email"),
        {"email": "admin@blingauto.com"}
    )
    row = result.first()
    print(f"Email: {row[0]}")
    print(f"Hash: {row[1]}")
