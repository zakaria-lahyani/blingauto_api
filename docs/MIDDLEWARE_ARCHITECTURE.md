# 🛡️ Middleware Architecture Strategy

## Overview

This document outlines the recommended middleware architecture for the Car Wash API, balancing global cross-cutting concerns with feature-specific business logic.

## 🎯 **Middleware Classification**

### **Global Middleware (App-Level)**
Applied to ALL requests, regardless of feature:

| Middleware | Purpose | Scope | Order Priority |
|------------|---------|--------|----------------|
| **CORS** | Cross-origin requests | All routes | 1 (First) |
| **Security Headers** | Security headers (HSTS, CSP, etc.) | All routes | 2 |
| **Trusted Host** | Host validation | All routes | 3 |
| **Request Logging** | Request/response logging | All routes | 4 |
| **Compression** | Response compression | All routes | 5 |
| **Error Handling** | Global error handling | All routes | 6 (Last) |

### **Feature-Specific Middleware (Router-Level)**
Applied only to specific feature routes:

| Feature | Middleware | Purpose | Scope |
|---------|------------|---------|--------|
| **Auth** | AuthRateLimiting | Login/registration limits | `/auth/*` only |
| **Auth** | AuthSecurityLogging | Security event logging | `/auth/*` only |
| **Booking** | BookingRateLimiting | Booking creation limits | `/booking/*` only |
| **Booking** | BookingAnalytics | Usage analytics | `/booking/*` only |
| **Payment** | PaymentSecurity | PCI compliance | `/payment/*` only |
| **Payment** | PaymentRateLimiting | Transaction limits | `/payment/*` only |

## 🏗️ **Implementation Strategy**

### **1. Global Middleware Setup**

Create a centralized middleware configuration:

```python
# shared/middleware/global_middleware.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware

def setup_global_middleware(app: FastAPI, config: GlobalConfig):
    """Setup global middleware for the entire application"""
    
    # 1. CORS (first - handles preflight requests)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Page-Count"]
    )
    
    # 2. Security Headers
    app.add_middleware(SecurityHeadersMiddleware, config=config.security)
    
    # 3. Trusted Host Validation
    if config.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=config.allowed_hosts
        )
    
    # 4. Request Logging & Metrics
    app.add_middleware(RequestLoggingMiddleware, config=config.logging)
    
    # 5. Response Compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 6. Global Error Handling (last)
    app.add_middleware(GlobalErrorHandlingMiddleware, config=config.error_handling)


# shared/middleware/security_headers.py
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        if self.config.enable_hsts:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
        return response


# shared/middleware/request_logging.py
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"{request.method} {request.url} - Started")
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        return response
```

### **2. Feature-Specific Middleware**

Keep feature middleware within their respective modules:

```python
# features/auth/presentation/middleware/auth_rate_limiting.py
class AuthRateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting specifically for auth endpoints"""
    
    def __init__(self, app, config: AuthConfig):
        super().__init__(app)
        self.config = config
        
    async def dispatch(self, request: Request, call_next):
        # Auth-specific rate limiting logic
        if not await self._check_auth_rate_limit(request):
            raise HTTPException(429, "Auth rate limit exceeded")
            
        return await call_next(request)

# features/booking/presentation/middleware/booking_analytics.py  
class BookingAnalyticsMiddleware(BaseHTTPMiddleware):
    """Analytics tracking for booking endpoints"""
    
    async def dispatch(self, request: Request, call_next):
        # Track booking-related metrics
        await self._track_booking_request(request)
        
        response = await call_next(request)
        
        await self._track_booking_response(request, response)
        return response
```

### **3. Main Application Setup**

```python
# main.py
from shared.middleware.global_middleware import setup_global_middleware
from shared.config import GlobalConfig

def create_app() -> FastAPI:
    app = FastAPI(
        title="Car Wash API",
        description="Feature-based car wash management system",
        version="1.0.0"
    )
    
    # Load global configuration
    global_config = GlobalConfig()
    
    # ✅ Setup global middleware FIRST
    setup_global_middleware(app, global_config)
    
    # ✅ Setup features (each adds their own middleware)
    auth_module = AuthModule(AuthConfig())
    auth_module.setup(app, prefix="/auth")
    
    booking_module = BookingModule(BookingConfig())
    booking_module.setup(app, prefix="/booking")
    
    payment_module = PaymentModule(PaymentConfig())
    payment_module.setup(app, prefix="/payment")
    
    # Health check (no specific middleware needed)
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app
```

## 🔧 **Configuration Management**

### **Global Configuration**

```python
# shared/config.py
class GlobalConfig(BaseSettings):
    """Global application configuration"""
    
    # CORS settings
    cors_origins: List[str] = Field(default=["http://localhost:3000"])
    
    # Security settings
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"])
    enable_hsts: bool = Field(default=True)
    
    # Logging settings
    log_level: str = Field(default="INFO")
    enable_request_logging: bool = Field(default=True)
    
    # Environment
    environment: str = Field(default="development")
    
    class Config:
        env_prefix = "GLOBAL_"
        env_file = ".env"
```

### **Feature Configuration**

```python
# features/auth/config.py
class AuthConfig(BaseSettings):
    """Auth-specific configuration"""
    
    # Rate limiting (auth-specific)
    enable_rate_limiting: bool = Field(default=True)
    login_rate_limit: int = Field(default=5)  # per minute
    
    # Security logging (auth-specific)
    enable_security_logging: bool = Field(default=True)
    log_failed_attempts: bool = Field(default=True)
    
    class Config:
        env_prefix = "AUTH_"
        env_file = ".env"
```

## 📊 **Middleware Execution Order**

### **Request Flow:**
```
1. CORS Middleware (Global)
   ↓
2. Security Headers (Global)
   ↓
3. Trusted Host (Global)
   ↓
4. Request Logging (Global)
   ↓
5. Compression (Global)
   ↓
6. Feature Router
   ↓
7. Auth Rate Limiting (Feature-specific)
   ↓
8. Auth Security Logging (Feature-specific)
   ↓
9. Route Handler
   ↓
10. Global Error Handling (Global)
```

### **Response Flow:**
```
Route Handler Response
   ↓
Feature Middleware (reverse order)
   ↓
Global Middleware (reverse order)
   ↓
Client
```

## ⚠️ **FastAPI Router Middleware Limitation**

**Important Note**: FastAPI routers (`APIRouter`) do **not** support middleware directly. Only the main `FastAPI` app supports the `add_middleware()` method.

### **Current Implementation:**
```python
# ❌ This doesn't work - routers don't have add_middleware()
router.add_middleware(AuthRateLimitingMiddleware)  # AttributeError

# ✅ This works - only on main app
app.add_middleware(SecurityHeadersMiddleware)  # OK
```

### **Solutions for Feature-Specific Logic:**

#### **Option 1: Route Dependencies (Current)**
```python
# Create dependency functions
def auth_rate_limit():
    async def dependency(request: Request):
        # Rate limiting logic here
        pass
    return dependency

# Apply to specific routes
@router.post("/login", dependencies=[Depends(auth_rate_limit())])
async def login(data: LoginData):
    pass
```

#### **Option 2: Custom Middleware with Path Filtering (Recommended)**
```python
# Global middleware that filters by path
class FeatureSpecificMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/auth/"):
            # Apply auth-specific logic
            pass
        elif request.url.path.startswith("/booking/"):
            # Apply booking-specific logic
            pass
        
        return await call_next(request)

# Add to main app
app.add_middleware(FeatureSpecificMiddleware)
```

## ✅ **Best Practices**

### **DO:**
- ✅ Use global middleware for cross-cutting concerns (CORS, security, logging)
- ✅ Use path-based filtering in global middleware for feature-specific logic
- ✅ Keep middleware configuration within feature modules
- ✅ Apply middleware in the correct order (CORS first, error handling last)
- ✅ Use environment-specific configuration
- ✅ Use route dependencies for endpoint-specific logic

### **DON'T:**
- ❌ Don't try to add middleware to routers (not supported)
- ❌ Don't duplicate global middleware in features
- ❌ Don't apply feature-specific logic globally without path filtering
- ❌ Don't hardcode middleware configuration
- ❌ Don't ignore middleware execution order
- ❌ Don't add heavy processing in middleware

## 🔍 **Example: Complete Middleware Stack**

```python
# For a request to POST /auth/login:

1. ✅ CORSMiddleware (Global) - Handles CORS headers
2. ✅ SecurityHeadersMiddleware (Global) - Adds security headers  
3. ✅ TrustedHostMiddleware (Global) - Validates host
4. ✅ RequestLoggingMiddleware (Global) - Logs request
5. ✅ GZipMiddleware (Global) - Compresses response
6. ✅ AuthRateLimitingMiddleware (Auth Feature) - Checks login rate limits
7. ✅ AuthSecurityLoggingMiddleware (Auth Feature) - Logs security events
8. 🎯 login_endpoint() - Actual route handler
9. ✅ GlobalErrorHandlingMiddleware (Global) - Handles any errors

# For a request to GET /health:

1. ✅ CORSMiddleware (Global)
2. ✅ SecurityHeadersMiddleware (Global)
3. ✅ TrustedHostMiddleware (Global)
4. ✅ RequestLoggingMiddleware (Global)
5. ✅ GZipMiddleware (Global)
6. 🎯 health_check() - No feature middleware
7. ✅ GlobalErrorHandlingMiddleware (Global)
```

This architecture ensures:
- **Global concerns** are handled consistently across all features
- **Feature-specific logic** doesn't affect other features
- **Easy maintenance** and **clear separation of concerns**
- **Performance** by avoiding redundant processing