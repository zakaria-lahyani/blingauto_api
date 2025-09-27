# 🛡️ Rate Limiting Architecture - Current Issues & Solutions

## 🚨 Current Issue Analysis

### **Problem: Global Rate Limiting Applied by Auth Feature**

The current implementation has a significant architectural flaw:

```python
# ❌ CURRENT IMPLEMENTATION (PROBLEMATIC)
# In auth_module.py
def setup(self, app, prefix: str = "/auth"):
    # ... setup auth routes
    
    # ❌ This applies rate limiting to the ENTIRE APP
    if self.config.enable_rate_limiting:
        app.add_middleware(RateLimitingMiddleware, config=self.config)
```

### **What This Means:**
- ✅ **Auth endpoints**: Get proper role-based rate limiting
- ❌ **Future booking endpoints**: Get auth rate limits (wrong!)  
- ❌ **Future payment endpoints**: Get auth rate limits (wrong!)
- ❌ **Health/docs endpoints**: Get auth rate limits (wrong!)

### **Example of the Problem:**
```python
# User makes requests:
POST /auth/login        # ✅ Correctly limited by auth config (30/min for client)
GET /booking/services   # ❌ Incorrectly limited by auth config (30/min for client)
POST /payment/charge    # ❌ Incorrectly limited by auth config (30/min for client)
GET /health            # ❌ Incorrectly limited by auth config (30/min for client)
```

## ✅ **Correct Architecture Solutions**

### **Option 1: Feature-Specific Rate Limiting (Recommended)**

Each feature should manage its own rate limiting:

```python
# ✅ SOLUTION 1: Feature-specific rate limiting

# Auth feature - only applies to /auth/* routes
class AuthModule:
    def setup(self, app, prefix: str = "/auth"):
        router = create_auth_router(self)
        
        # Apply auth-specific rate limiting to auth router only
        if self.config.enable_rate_limiting:
            router.add_middleware(AuthRateLimitingMiddleware, config=self.config)
        
        app.include_router(router, prefix=prefix)

# Booking feature - only applies to /booking/* routes  
class BookingModule:
    def setup(self, app, prefix: str = "/booking"):
        router = create_booking_router(self)
        
        # Apply booking-specific rate limiting to booking router only
        if self.config.enable_rate_limiting:
            router.add_middleware(BookingRateLimitingMiddleware, config=self.config)
        
        app.include_router(router, prefix=prefix)
```

### **Option 2: Centralized Rate Limiting Service (Advanced)**

```python
# ✅ SOLUTION 2: Centralized rate limiting service

class RateLimitingService:
    def __init__(self):
        self.feature_configs = {}
    
    def register_feature(self, prefix: str, config: FeatureRateLimitConfig):
        """Register feature-specific rate limiting rules"""
        self.feature_configs[prefix] = config
    
    def check_rate_limit(self, path: str, user: User) -> bool:
        """Apply appropriate rate limiting based on path"""
        
        # Determine which feature this path belongs to
        if path.startswith("/auth"):
            config = self.feature_configs.get("/auth")
        elif path.startswith("/booking"):
            config = self.feature_configs.get("/booking")
        elif path.startswith("/payment"):
            config = self.feature_configs.get("/payment")
        else:
            config = self.default_config
        
        return self._apply_rate_limit(path, user, config)

# Usage in main.py
rate_limiter = RateLimitingService()

# Features register their rate limiting rules
auth_module.register_rate_limiting(rate_limiter, "/auth")
booking_module.register_rate_limiting(rate_limiter, "/booking")

# Apply centralized middleware
app.add_middleware(CentralizedRateLimitingMiddleware, service=rate_limiter)
```

### **Option 3: Dependency-Based Rate Limiting (FastAPI Native)**

```python
# ✅ SOLUTION 3: Dependency-based rate limiting per endpoint

# Auth endpoints
@router.post("/login")
async def login(
    request: LoginRequest,
    _: None = Depends(auth_rate_limit(limit=5, window=60))  # Auth-specific limit
):
    pass

# Booking endpoints  
@router.post("/reservations")
async def create_booking(
    request: BookingRequest,
    current_user: AuthUser = Depends(get_current_user),
    _: None = Depends(booking_rate_limit(limit=10, window=60))  # Booking-specific limit
):
    pass

# Payment endpoints
@router.post("/charge")
async def process_payment(
    request: PaymentRequest,
    current_user: AuthUser = Depends(get_current_user),
    _: None = Depends(payment_rate_limit(limit=3, window=60))  # Payment-specific limit
):
    pass
```

## 🎯 **Recommended Implementation**

### **Feature-Specific Rate Limiting with Router Middleware**

Let me show the corrected implementation:

```python
# ✅ CORRECTED: Auth feature rate limiting
# src/features/auth/presentation/middleware/auth_rate_limiter.py

class AuthRateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware specifically for auth endpoints"""
    
    def __init__(self, app, config: AuthConfig):
        super().__init__(app)
        self.config = config
        self.rate_limiter = AuthRateLimiter(config)
    
    async def dispatch(self, request: Request, call_next):
        """Apply auth-specific rate limiting"""
        
        if not self.config.enable_rate_limiting:
            return await call_next(request)
        
        # Only applies to auth endpoints since it's on auth router
        if not await self.rate_limiter.check_auth_rate_limit(request):
            raise HTTPException(
                status_code=429,
                detail="Auth rate limit exceeded",
                headers={"Retry-After": "60"}
            )
        
        return await call_next(request)


# ✅ CORRECTED: Auth module setup
class AuthModule:
    def setup(self, app, prefix: str = "/auth"):
        """Setup auth module with FastAPI app"""
        from .presentation.api.router import create_auth_router
        
        # Create auth router
        router = create_auth_router(self)
        
        # Apply auth-specific rate limiting to auth router ONLY
        if self.config.enable_rate_limiting:
            from .presentation.middleware.auth_rate_limiter import AuthRateLimitingMiddleware
            router.add_middleware(AuthRateLimitingMiddleware, config=self.config)
        
        # Add router to app (rate limiting only applies to /auth/* routes)
        app.include_router(router, prefix=prefix, tags=["Authentication"])
        
        logger.info(f"Auth module setup complete with prefix: {prefix}")
```

### **Configuration Per Feature**

```python
# Auth feature configuration
class AuthConfig(BaseSettings):
    # Auth-specific rate limits
    auth_login_limit: int = Field(default=5)        # 5 login attempts per minute
    auth_register_limit: int = Field(default=3)     # 3 registration attempts per minute
    auth_password_reset_limit: int = Field(default=2)  # 2 password resets per hour
    
    # Role-based limits for auth endpoints
    admin_auth_limit: int = Field(default=100)      # Admins: 100 auth requests/min
    client_auth_limit: int = Field(default=20)      # Clients: 20 auth requests/min

# Booking feature configuration  
class BookingConfig(BaseSettings):
    # Booking-specific rate limits
    booking_creation_limit: int = Field(default=5)   # 5 bookings per hour
    booking_modification_limit: int = Field(default=10)  # 10 modifications per hour
    service_browsing_limit: int = Field(default=100) # 100 service views per hour

# Payment feature configuration
class PaymentConfig(BaseSettings):
    # Payment-specific rate limits (more restrictive)
    payment_processing_limit: int = Field(default=3) # 3 payments per minute
    refund_request_limit: int = Field(default=1)     # 1 refund per hour
```

### **Rate Limiting Matrix**

| Feature | Endpoints | Rate Limits | Applied To |
|---------|-----------|-------------|------------|
| **Auth** | `/auth/*` | Login: 5/min<br>Register: 3/min<br>Reset: 2/hour | Auth router only |
| **Booking** | `/booking/*` | Create: 5/hour<br>Modify: 10/hour<br>Browse: 100/hour | Booking router only |
| **Payment** | `/payment/*` | Process: 3/min<br>Refund: 1/hour | Payment router only |
| **Global** | All other endpoints | Health: unlimited<br>Docs: unlimited | App-level (optional) |

## 🔧 **Implementation Priority**

### **Immediate Fix (Current Issue)**
1. **Move rate limiting from app-level to router-level** in auth module
2. **Make rate limiting apply only to auth endpoints**
3. **Test that other endpoints are not affected**

### **Future Enhancement (New Features)**
1. **Each new feature implements its own rate limiting**
2. **Feature-specific rate limiting configurations**
3. **Clear documentation of rate limiting per feature**

## 📊 **Impact Analysis**

### **Current Impact:**
```python
# ❌ BEFORE FIX: All endpoints get auth rate limiting
GET /health          # Limited by auth config (wrong!)
GET /docs           # Limited by auth config (wrong!)  
POST /auth/login    # Limited by auth config (correct)
Future: POST /booking/create  # Would be limited by auth config (wrong!)
```

### **After Fix:**
```python
# ✅ AFTER FIX: Only auth endpoints get auth rate limiting
GET /health          # No rate limiting (correct!)
GET /docs           # No rate limiting (correct!)
POST /auth/login    # Limited by auth config (correct!)
Future: POST /booking/create  # Limited by booking config (correct!)
```

## 🎯 **Next Steps**

1. **Immediate**: Fix the current auth module to apply rate limiting only to auth routes
2. **Documentation**: Update docs to clarify rate limiting scope
3. **Future Features**: Implement feature-specific rate limiting from the start
4. **Testing**: Verify rate limiting behavior per feature

This ensures that each feature has appropriate rate limiting without affecting other parts of the application.