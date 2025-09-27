# 🚀 Auth Module - Standalone Integration Guide

## Overview

This refactored auth module is now a **complete standalone package** that can be dropped into any FastAPI application with just **3 lines of code**. 

## ✅ Complete Features

- **User Registration** with email verification
- **Secure Login** with account lockout protection
- **Password Reset** with secure token flow
- **JWT Token Management** with automatic rotation
- **Role-Based Access Control** (Admin, Manager, Washer, Client)
- **Rate Limiting** per user role
- **Environment-based Admin Setup**
- **Production-ready Security** features

## 🎯 Integration Steps

### 1. Copy the Auth Module

```bash
# Copy to your new project
cp -r src/features/auth/ new_project/src/features/auth/
cp -r src/shared/ new_project/src/shared/
cp requirements.txt new_project/
cp .env.example new_project/.env
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Edit .env file
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/your_db
AUTH_JWT_SECRET_KEY=your-super-secret-key
AUTH_INITIAL_ADMIN_EMAIL=admin@yourapp.com
AUTH_INITIAL_ADMIN_PASSWORD=admin123
```

### 4. Integrate with FastAPI

```python
from fastapi import FastAPI
from features.auth import AuthModule, AuthConfig
from shared.database import init_database

def create_app():
    app = FastAPI(title="Your App")
    
    # Initialize database
    init_database()
    
    # Setup auth module - THIS IS ALL YOU NEED! 🎉
    auth = AuthModule(AuthConfig())
    auth.setup(app, prefix="/auth")
    
    # Initialize on startup
    @app.on_event("startup")
    async def startup():
        await auth.initialize()
    
    return app

app = create_app()
```

### 5. Use Auth Dependencies in Custom Endpoints

```python
from fastapi import Depends
from features.auth import AuthUser, AuthRole

# Get the auth module instance
auth = app.state.auth  # or store it globally

@app.get("/protected")
async def protected_endpoint(user: AuthUser = Depends(auth.get_current_user)):
    return {"user": user.email}

@app.get("/admin-only")  
async def admin_only(user: AuthUser = Depends(auth.get_current_admin)):
    return {"message": "Admin access granted"}

@app.get("/manager-plus")
async def manager_plus(user: AuthUser = Depends(auth.get_current_manager)):
    return {"message": "Manager or admin access"}

@app.get("/washer-only")
async def washer_only(user: AuthUser = Depends(auth.require_role(AuthRole.WASHER))):
    return {"message": "Washer access granted"}
```

## 📋 Available Endpoints

Once integrated, these endpoints are automatically available:

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh tokens
- `POST /auth/logout` - Logout single device
- `POST /auth/logout-all` - Logout all devices

### Email Verification
- `POST /auth/verify-email/request` - Request verification email
- `POST /auth/verify-email/confirm` - Confirm email with token

### Password Management
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password with token
- `POST /auth/change-password` - Change password (authenticated)

### User Management
- `GET /auth/me` - Get current user profile
- `PUT /auth/me` - Update current user profile
- `GET /auth/users` - List users (Manager/Admin)
- `GET /auth/users/{id}` - Get user details (Manager/Admin)
- `PUT /auth/users/{id}/role` - Change user role (Manager/Admin)
- `DELETE /auth/users/{id}` - Delete user (Admin only)

### System
- `GET /auth/features` - Get auth feature status

## 🔧 Configuration Options

```python
from features.auth import AuthConfig, AuthFeature

config = AuthConfig(
    # Core settings
    jwt_secret_key="your-secret-key",
    access_token_expire_minutes=15,
    refresh_token_expire_days=7,
    
    # Database
    database_url="postgresql+asyncpg://...",
    table_prefix="auth_",
    
    # Features (enable/disable as needed)
    enabled_features=[
        AuthFeature.EMAIL_VERIFICATION,
        AuthFeature.PASSWORD_RESET,
        AuthFeature.ACCOUNT_LOCKOUT,
        AuthFeature.TOKEN_ROTATION,
        AuthFeature.RATE_LIMITING,
        AuthFeature.ADMIN_SETUP
    ],
    
    # Security settings
    max_login_attempts=5,
    initial_lockout_minutes=5,
    max_lockout_minutes=60,
    
    # Rate limiting
    admin_rate_limit=200,
    client_rate_limit=30,
    
    # Admin setup
    initial_admin_email="admin@yourapp.com",
    initial_admin_password="admin123"
)
```

## 👥 User Roles & Permissions

| Role | Permissions |
|------|------------|
| **Admin** | Full system access, manage all users |
| **Manager** | Manage washers and clients, view reports |
| **Washer** | Manage assigned washes, update status |
| **Client** | Manage own bookings and profile |

### Role Hierarchy
- Admin can manage: Everyone
- Manager can manage: Washers, Clients  
- Washer can manage: Own profile
- Client can manage: Own profile

## 🔒 Security Features

### Account Protection
- **Progressive Lockout**: 5min → 10min → 20min → 60min max
- **Brute Force Protection**: Account lockout after failed attempts
- **Rate Limiting**: Different limits per user role

### Token Security
- **JWT Rotation**: Automatic refresh token rotation
- **Token Families**: Detects token reuse attacks
- **Secure Storage**: Hashed tokens in database

### Password Security
- **Bcrypt Hashing**: Secure password storage
- **Reset Tokens**: Time-limited, single-use tokens
- **Verification Flow**: Email verification required

## ✅ Testing

```bash
# Test the integration
python test_standalone.py

# Test with full database
python auth_module_check.py

# Run the application
python main.py
```

## 🎉 Benefits

- ✅ **Self-Contained**: All auth logic in one module
- ✅ **Zero Dependencies**: No external auth requirements
- ✅ **Configuration-Driven**: Enable/disable features easily
- ✅ **Production-Ready**: Enterprise security features
- ✅ **Well-Tested**: Comprehensive test coverage
- ✅ **Easy Integration**: 3-line setup
- ✅ **Reusable**: Copy to any new project

## 🚀 You're Ready!

Your standalone auth module is now ready for production use and can be easily copied to new projects. The integration is so simple that you can have a fully-featured authentication system running in minutes!

**Happy coding!** 🎉