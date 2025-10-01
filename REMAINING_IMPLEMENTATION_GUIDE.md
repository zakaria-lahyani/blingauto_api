# Remaining Implementation Guide

**Date:** 2025-10-01
**Priority:** HIGH - Final production requirements

---

## Overview

Three critical tasks remain for full production readiness:

1. ✅ **COMPLETE** - 8 Booking Use Cases + API Endpoints (~1,500 lines)
2. ⚠️ **TODO** - 3 Missing Auth Endpoints (~200 lines)
3. ⚠️ **TODO** - Replace 5 Stub Services (~400 lines)

**Estimated Total:** ~600 lines remaining

---

## TASK 1: Add Missing Auth Endpoints ⚠️

### 1.1 POST `/api/v1/auth/change-password`

**Purpose:** Allow authenticated users to change their password

**Schema to Add** (`app/features/auth/api/schemas.py`):
```python
class ChangePasswordRequest(BaseModel):
    """Schema for changing password."""
    current_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

    @validator('new_password')
    def password_strength(cls, v, values):
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('New password must be different from current password')
        # Add strength validation: uppercase, lowercase, number, special char
        return v

class ChangePasswordResponse(BaseModel):
    """Schema for change password response."""
    message: str = Field(..., description="Success message")
    changed_at: datetime = Field(..., description="Password change timestamp")
```

**Use Case to Create** (`app/features/auth/use_cases/change_password.py`):
```python
from dataclasses import dataclass
from datetime import datetime
from app.core.errors import ValidationError, AuthenticationError
from app.features.auth.ports import IUserRepository, IPasswordHasher

@dataclass
class ChangePasswordRequest:
    user_id: str
    current_password: str
    new_password: str

@dataclass
class ChangePasswordResponse:
    message: str
    changed_at: datetime

class ChangePasswordUseCase:
    """Use case for changing user password."""

    def __init__(
        self,
        user_repository: IUserRepository,
        password_hasher: IPasswordHasher,
    ):
        self._user_repository = user_repository
        self._password_hasher = password_hasher

    def execute(self, request: ChangePasswordRequest) -> ChangePasswordResponse:
        # 1. Get user
        user = self._user_repository.get_by_id(request.user_id)
        if not user:
            raise AuthenticationError("User not found")

        # 2. Verify current password
        if not self._password_hasher.verify(request.current_password, user.hashed_password):
            raise ValidationError("Current password is incorrect")

        # 3. Hash new password
        new_hash = self._password_hasher.hash(request.new_password)

        # 4. Update user
        user.hashed_password = new_hash
        user.updated_at = datetime.utcnow()
        self._user_repository.update(user)

        return ChangePasswordResponse(
            message="Password changed successfully",
            changed_at=user.updated_at
        )
```

**Router Endpoint to Add** (`app/features/auth/api/router.py`):
```python
@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request_data: ChangePasswordRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """Change user password (authenticated users only)."""
    user_repo = UserRepository(db)
    password_hasher = PasswordHasherAdapter()

    use_case = ChangePasswordUseCase(user_repo, password_hasher)

    try:
        request = ChangePasswordUseCaseRequest(
            user_id=current_user.id,
            current_password=request_data.current_password,
            new_password=request_data.new_password,
        )
        response = use_case.execute(request)
        return ChangePasswordResponse(
            message=response.message,
            changed_at=response.changed_at
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
```

---

### 1.2 PUT `/api/v1/auth/profile`

**Purpose:** Allow users to update their profile information

**Schema to Add** (`app/features/auth/api/schemas.py`):
```python
class UpdateProfileRequest(BaseModel):
    """Schema for updating user profile."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)

    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Name cannot be empty')
            return v.strip().title()
        return v

class UpdateProfileResponse(BaseModel):
    """Schema for update profile response."""
    user_id: str
    first_name: str
    last_name: str
    phone_number: Optional[str]
    updated_at: datetime
```

**Use Case to Create** (`app/features/auth/use_cases/update_profile.py`):
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from app.core.errors import NotFoundError, ValidationError

@dataclass
class UpdateProfileRequest:
    user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None

@dataclass
class UpdateProfileResponse:
    user_id: str
    first_name: str
    last_name: str
    phone_number: Optional[str]
    updated_at: datetime

class UpdateProfileUseCase:
    """Use case for updating user profile."""

    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository

    def execute(self, request: UpdateProfileRequest) -> UpdateProfileResponse:
        # 1. Get user
        user = self._user_repository.get_by_id(request.user_id)
        if not user:
            raise NotFoundError(f"User {request.user_id} not found")

        # 2. Update fields
        if request.first_name is not None:
            user.first_name = request.first_name
        if request.last_name is not None:
            user.last_name = request.last_name
        if request.phone_number is not None:
            user.phone_number = request.phone_number

        user.updated_at = datetime.utcnow()

        # 3. Save
        updated_user = self._user_repository.update(user)

        return UpdateProfileResponse(
            user_id=updated_user.id,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            phone_number=updated_user.phone_number,
            updated_at=updated_user.updated_at
        )
```

**Router Endpoint:**
```python
@router.put("/profile", response_model=UpdateProfileResponse)
async def update_profile(
    profile_data: UpdateProfileRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """Update user profile (authenticated users only)."""
    user_repo = UserRepository(db)
    use_case = UpdateProfileUseCase(user_repo)

    try:
        request = UpdateProfileUseCaseRequest(
            user_id=current_user.id,
            first_name=profile_data.first_name,
            last_name=profile_data.last_name,
            phone_number=profile_data.phone_number,
        )
        response = use_case.execute(request)
        return UpdateProfileResponse(**response.__dict__)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
```

---

### 1.3 POST `/api/v1/auth/logout`

**Purpose:** Logout user and invalidate all refresh tokens

**Schema to Add** (`app/features/auth/api/schemas.py`):
```python
class LogoutResponse(BaseModel):
    """Schema for logout response."""
    message: str = Field(..., description="Logout success message")
    tokens_invalidated: int = Field(..., description="Number of tokens invalidated")
```

**Use Case to Create** (`app/features/auth/use_cases/logout.py`):
```python
from dataclasses import dataclass
from app.core.errors import NotFoundError

@dataclass
class LogoutRequest:
    user_id: str

@dataclass
class LogoutResponse:
    message: str
    tokens_invalidated: int

class LogoutUseCase:
    """Use case for logging out user (invalidate all refresh tokens)."""

    def __init__(
        self,
        refresh_token_repository: IRefreshTokenRepository,
        cache_service: ICacheService,
    ):
        self._refresh_token_repository = refresh_token_repository
        self._cache_service = cache_service

    def execute(self, request: LogoutRequest) -> LogoutResponse:
        # 1. Get all refresh tokens for user
        tokens = self._refresh_token_repository.get_by_user_id(request.user_id)

        # 2. Revoke all tokens
        count = 0
        for token in tokens:
            token.is_revoked = True
            self._refresh_token_repository.update(token)
            count += 1

        # 3. Clear user cache
        self._cache_service.delete(f"user:{request.user_id}")

        return LogoutResponse(
            message="Logged out successfully",
            tokens_invalidated=count
        )
```

**Router Endpoint:**
```python
@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """Logout user and invalidate all refresh tokens."""
    refresh_token_repo = RefreshTokenRepository(db)
    cache_service = RedisCacheService()  # TODO: Use real cache

    use_case = LogoutUseCase(refresh_token_repo, cache_service)

    try:
        request = LogoutUseCaseRequest(user_id=current_user.id)
        response = use_case.execute(request)
        return LogoutResponse(
            message=response.message,
            tokens_invalidated=response.tokens_invalidated
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )
```

---

## TASK 2: Replace Stub Services ⚠️

### 2.1 Email Service (Real SMTP Implementation)

**Location:** `app/core/email/service.py`

**Current Stub:**
```python
# app/features/bookings/api/dependencies.py:6-11
class StubEmailService:
    def send_email(self, *args, **kwargs):
        pass
```

**Real Implementation:**
```python
# app/core/email/service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from app.core.config.settings import settings

class EmailService:
    """Real SMTP email service."""

    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email

    def send_email(
        self,
        to: List[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> bool:
        """Send email via SMTP."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to)

            # Add text part
            msg.attach(MIMEText(body_text, 'plain'))

            # Add HTML part if provided
            if body_html:
                msg.attach(MIMEText(body_html, 'html'))

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            return True
        except Exception as e:
            # Log error
            print(f"Email send failed: {e}")
            return False
```

**Configuration to Add** (`app/core/config/settings.py`):
```python
# Email settings
smtp_host: str = Field(default="localhost", env="SMTP_HOST")
smtp_port: int = Field(default=587, env="SMTP_PORT")
smtp_user: str = Field(default="", env="SMTP_USER")
smtp_password: str = Field(default="", env="SMTP_PASSWORD")
from_email: str = Field(default="noreply@example.com", env="FROM_EMAIL")
```

**Environment Variables** (`.env`):
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourcompany.com
```

**Update Dependency:**
```python
# app/features/bookings/api/dependencies.py
from app.core.email import EmailService

def get_email_service():
    """Get real email service."""
    return EmailService()
```

---

### 2.2 Cache Service (Redis Implementation)

**Location:** `app/core/cache/redis_service.py`

**Current Stub:**
```python
class StubCacheService:
    def get(self, *args, **kwargs):
        return None
    def set(self, *args, **kwargs):
        pass
```

**Real Implementation:**
```python
# app/core/cache/redis_service.py
import redis
import json
from typing import Optional, Any
from app.core.config.settings import settings

class RedisCacheService:
    """Real Redis cache service."""

    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
            decode_responses=True,
        )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL."""
        try:
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache invalidate error: {e}")
            return 0
```

**Configuration:**
```python
# app/core/config/settings.py
redis_host: str = Field(default="localhost", env="REDIS_HOST")
redis_port: int = Field(default=6379, env="REDIS_PORT")
redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
redis_db: int = Field(default=0, env="REDIS_DB")
```

**Environment Variables:**
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0
```

---

### 2.3 Lock Service (Redis Distributed Locks)

**Location:** `app/core/locks/redis_lock.py`

**Current Stub:**
```python
class StubLockService:
    def acquire_lock(self, *args, **kwargs):
        return True
    def release_lock(self, *args, **kwargs):
        pass
```

**Real Implementation:**
```python
# app/core/locks/redis_lock.py
import redis
import uuid
import time
from typing import Optional
from app.core.config.settings import settings

class RedisLockService:
    """Real Redis distributed lock service."""

    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db + 1,  # Use separate DB for locks
        )

    def acquire_lock(
        self,
        resource: str,
        timeout: int = 30,
        retry_times: int = 3,
        retry_delay: float = 0.1,
    ) -> Optional[str]:
        """Acquire distributed lock."""
        lock_key = f"lock:{resource}"
        lock_value = str(uuid.uuid4())

        for _ in range(retry_times):
            # Try to acquire lock with NX (only if not exists) and EX (expiry)
            acquired = self.client.set(
                lock_key,
                lock_value,
                nx=True,
                ex=timeout
            )

            if acquired:
                return lock_value

            # Wait before retry
            time.sleep(retry_delay)

        return None

    def release_lock(self, resource: str, lock_value: str) -> bool:
        """Release distributed lock."""
        lock_key = f"lock:{resource}"

        # Lua script to ensure we only delete our own lock
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        try:
            result = self.client.eval(lua_script, 1, lock_key, lock_value)
            return bool(result)
        except Exception as e:
            print(f"Lock release error: {e}")
            return False
```

**Usage Example:**
```python
# In RescheduleBookingUseCase
lock_id = self._lock_service.acquire_lock(
    resource=f"booking_slot:{new_scheduled_at}:{booking_type}",
    timeout=30,
)

if not lock_id:
    raise BusinessRuleViolationError("Time slot is locked")

try:
    # Check conflicts and update booking
    pass
finally:
    self._lock_service.release_lock(
        resource=f"booking_slot:{new_scheduled_at}:{booking_type}",
        lock_value=lock_id
    )
```

---

### 2.4 Event Service (In-Memory Event Bus)

**Location:** `app/core/events/event_bus.py`

**Current Stub:**
```python
class StubEventService:
    def publish(self, *args, **kwargs):
        pass
```

**Real Implementation (Simple In-Memory):**
```python
# app/core/events/event_bus.py
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class Event:
    """Domain event."""
    name: str
    data: Dict[str, Any]
    timestamp: datetime
    aggregate_id: str

class EventBus:
    """Simple in-memory event bus."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_name: str, handler: Callable):
        """Subscribe handler to event."""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)

    def publish(self, event: Event):
        """Publish event to all subscribers."""
        if event.name in self._handlers:
            for handler in self._handlers[event.name]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Event handler error: {e}")

    async def publish_async(self, event: Event):
        """Publish event asynchronously."""
        if event.name in self._handlers:
            tasks = []
            for handler in self._handlers[event.name]:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(event))
                else:
                    tasks.append(asyncio.to_thread(handler, event))

            await asyncio.gather(*tasks, return_exceptions=True)

# Global event bus instance
_event_bus = EventBus()

def get_event_bus() -> EventBus:
    """Get global event bus instance."""
    return _event_bus
```

**Usage Example:**
```python
# In booking adapters/services.py
class EventBusService:
    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus

    def publish_booking_confirmed(self, booking, confirmed_by):
        event = Event(
            name="booking.confirmed",
            data={
                "booking_id": booking.id,
                "customer_id": booking.customer_id,
                "confirmed_by": confirmed_by,
            },
            timestamp=datetime.utcnow(),
            aggregate_id=booking.id,
        )
        self._event_bus.publish(event)
```

---

### 2.5 Update All Dependencies to Use Real Services

**File:** `app/features/bookings/api/dependencies.py`

**Replace stubs (lines 6-36) with:**
```python
from app.core.email import EmailService
from app.core.cache import RedisCacheService
from app.core.events import get_event_bus, EventBus
from app.core.locks import RedisLockService

def get_email_service():
    """Get real email service."""
    return EmailService()

def get_cache_service():
    """Get real Redis cache service."""
    return RedisCacheService()

def get_event_service():
    """Get real event bus."""
    return get_event_bus()

def get_lock_service():
    """Get real Redis lock service."""
    return RedisLockService()
```

---

## Summary

### Files to Create: 17

**Auth Endpoints (6 files):**
1. `app/features/auth/use_cases/change_password.py`
2. `app/features/auth/use_cases/update_profile.py`
3. `app/features/auth/use_cases/logout.py`
4. Updates to `app/features/auth/api/schemas.py`
5. Updates to `app/features/auth/api/router.py`
6. Updates to `app/features/auth/use_cases/__init__.py`

**Core Services (8 files):**
7. `app/core/email/__init__.py`
8. `app/core/email/service.py`
9. `app/core/cache/__init__.py`
10. `app/core/cache/redis_service.py`
11. `app/core/locks/__init__.py`
12. `app/core/locks/redis_lock.py`
13. `app/core/events/__init__.py`
14. `app/core/events/event_bus.py`

**Configuration (2 files):**
15. Update `app/core/config/settings.py`
16. Update `.env.example`

**Dependencies (1 file):**
17. Update `app/features/bookings/api/dependencies.py`

---

### Estimated Effort

| Task | Lines | Time | Priority |
|------|-------|------|----------|
| Auth Endpoints | ~200 | 2-3h | HIGH |
| Email Service | ~100 | 1h | HIGH |
| Cache Service | ~100 | 1h | MEDIUM |
| Lock Service | ~80 | 1h | MEDIUM |
| Event Service | ~100 | 1h | LOW |
| **TOTAL** | **~580** | **6-8h** | |

---

### Dependencies to Install

```bash
pip install redis python-dotenv
```

**Update requirements.txt:**
```
redis==5.0.1
python-dotenv==1.0.0
```

---

## Testing Checklist

- [ ] Test change-password endpoint
- [ ] Test update-profile endpoint
- [ ] Test logout endpoint
- [ ] Test email sending (SMTP)
- [ ] Test Redis cache get/set
- [ ] Test Redis distributed locks
- [ ] Test event bus publish/subscribe
- [ ] Load test with real services

---

**Status:** 📋 Implementation guide complete - Ready to execute
**Next:** Implement auth endpoints first, then replace stub services
