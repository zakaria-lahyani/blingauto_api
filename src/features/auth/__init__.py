"""
Authentication Feature Module - Standalone & Reusable

Complete authentication system ready to drop into any FastAPI app:

🔐 FEATURES:
- User registration with email verification
- Secure login with account lockout protection  
- Password reset flow with secure tokens
- JWT token management with automatic rotation
- Role-based access control (Admin, Manager, Washer, Client)
- Rate limiting per user role
- Environment-based admin setup

🚀 INTEGRATION:
    from features.auth import AuthModule, AuthConfig
    
    # 1. Create auth module
    auth = AuthModule(AuthConfig())
    
    # 2. Setup with FastAPI app
    auth.setup(app, prefix="/auth")
    
    # 3. Initialize (in startup event)
    await auth.initialize()
    
    # That's it! All auth endpoints are now available 🎉

📋 AVAILABLE ENDPOINTS:
- POST /auth/register - Register new user
- POST /auth/login - User login  
- POST /auth/refresh - Refresh tokens
- POST /auth/logout - Logout single device
- POST /auth/logout-all - Logout all devices
- POST /auth/verify-email/request - Request verification email
- POST /auth/verify-email/confirm - Confirm email with token
- POST /auth/forgot-password - Request password reset
- POST /auth/reset-password - Reset password with token
- POST /auth/change-password - Change password (authenticated)
- GET /auth/me - Get current user profile
- PUT /auth/me - Update current user profile
- GET /auth/users - List users (Manager/Admin)
- GET /auth/users/{id} - Get user details (Manager/Admin)
- PUT /auth/users/{id}/role - Change user role (Manager/Admin)
- DELETE /auth/users/{id} - Delete user (Admin only)
- GET /auth/features - Get auth feature status

🎯 DEPENDENCIES FOR CUSTOM ENDPOINTS:
Access via the auth module instance:
    auth = AuthModule(AuthConfig())
    
    # Use in your custom endpoints
    @app.get("/custom-endpoint")
    async def custom_endpoint(user: AuthUser = Depends(auth.get_current_user)):
        return {"user": user.email}
    
    @app.get("/admin-only")  
    async def admin_only(user: AuthUser = Depends(auth.get_current_admin)):
        return {"message": "Admin access granted"}
    
    @app.get("/manager-plus")
    async def manager_plus(user: AuthUser = Depends(auth.get_current_manager)):
        return {"message": "Manager or admin access granted"}
        
    @app.get("/washer-only")
    async def washer_only(user: AuthUser = Depends(auth.require_role(AuthRole.WASHER))):
        return {"message": "Washer access granted"}
"""

from src.features.auth.config import AuthConfig, AuthFeature
from src.features.auth.auth_module import AuthModule
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole

__all__ = [
    # Core module
    'AuthModule', 
    'AuthConfig', 
    'AuthFeature',
    
    # Domain entities
    'AuthUser', 
    'AuthRole'
]