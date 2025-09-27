# Refactored Car Wash API - Feature-Based Architecture

## 🎯 Overview

This is a complete refactoring of the car wash API using **feature-based architecture**. The auth module has been extracted into a self-contained, reusable component with enterprise-grade security features.

## 🏗️ Architecture

### Feature-Based Structure
```
src/
├── shared/                    # Shared utilities
│   ├── database/             # Database session management
│   ├── events/               # Event bus for inter-module communication
│   └── ...
├── features/                 # Feature modules
│   └── auth/                 # Authentication feature module
│       ├── domain/           # Auth business logic
│       ├── application/      # Auth services
│       ├── infrastructure/   # Auth data & security
│       └── presentation/     # Auth API endpoints
└── core/                     # Application core
    └── app.py               # FastAPI app factory
```

### Auth Module Features
- ✅ **User Registration** with email verification
- ✅ **Secure Login** with account lockout protection
- ✅ **Password Reset** with secure token flow
- ✅ **JWT Token Management** with automatic rotation
- ✅ **Role-Based Access Control** (Admin, Manager, Washer, Client)
- ✅ **Rate Limiting** per user role
- ✅ **Admin Setup** via environment variables
- ✅ **Email Verification** system with professional templates
- ✅ **SMTP Integration** (Gmail, SendGrid, AWS SES, Custom)
- ✅ **Account Security** features

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment

#### For Development (Mock Emails)
```bash
cp env-templates/development.env .env
```

#### For Production (Real Emails)
```bash
# Gmail setup (5 minutes)
cp env-templates/gmail.env .env
# See docs/GMAIL_SETUP_QUICK_GUIDE.md

# Or SendGrid setup
cp env-templates/sendgrid.env .env
# See docs/EMAIL_SETUP_GUIDE.md
```

### 3. Run the Application
```bash
python src/main.py
```

### 4. Access the API
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Auth Features**: http://localhost:8000/auth/features

## 📋 API Endpoints

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

## 📧 Email System

The API includes a complete email verification system with professional templates:

### Email Features
- ✅ **Registration Verification** - Beautiful branded emails with secure links
- ✅ **Password Reset** - Secure reset emails with 2-hour expiry
- ✅ **Welcome Emails** - Sent after successful verification
- ✅ **Security Notifications** - Password change confirmations

### Supported Providers
- **Mock** (Development) - Logs emails to console
- **Gmail** (Small projects) - 500 emails/day free
- **SendGrid** (Production) - 100 emails/day free
- **AWS SES** (Enterprise) - $0.10 per 1,000 emails

### Quick Setup
```bash
# Development (no SMTP needed)
cp env-templates/development.env .env

# Production with Gmail
cp env-templates/gmail.env .env
# See docs/GMAIL_SETUP_QUICK_GUIDE.md for 5-minute setup
```

📚 **[Complete Email Documentation](docs/EMAIL_README.md)**

## ⚙️ Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./refactored_carwash.db

# JWT Settings
AUTH_JWT_SECRET_KEY=your-secret-key
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=15
AUTH_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Settings (see email documentation)
AUTH_EMAIL_PROVIDER=mock  # or smtp for production
AUTH_FROM_EMAIL=noreply@yourcompany.com
AUTH_APP_URL=https://yourcompany.com

# Admin Setup
AUTH_INITIAL_ADMIN_EMAIL=admin@carwash.com
AUTH_INITIAL_ADMIN_PASSWORD=admin123

# Features
AUTH_ENABLED_FEATURES=["email_verification","password_reset","account_lockout"]

# Rate Limiting
AUTH_ENABLE_RATE_LIMITING=true
AUTH_ADMIN_RATE_LIMIT=200
AUTH_CLIENT_RATE_LIMIT=30

# Security
AUTH_MAX_LOGIN_ATTEMPTS=5
AUTH_INITIAL_LOCKOUT_MINUTES=5
```

### Feature Configuration

You can enable/disable auth features:

```python
from features.auth import AuthConfig, AuthFeature

config = AuthConfig(
    enabled_features=[
        AuthFeature.EMAIL_VERIFICATION,
        AuthFeature.PASSWORD_RESET,
        AuthFeature.ACCOUNT_LOCKOUT,
        AuthFeature.TOKEN_ROTATION,
        AuthFeature.RATE_LIMITING
    ]
)
```

## 🧪 Testing

### Test Email System
```bash
# Test email service configuration
python quick_email_test.py

# Test complete email integration
python test_email_integration.py
```

### Run Auth Module Test
```bash
python auth_module_check.py
```

### Run Complete Test Suite
```bash
# Run all tests with coverage
python run_tests.py integration

# Run smoke tests (quick validation)
python run_tests.py smoke

# Run security tests
python run_tests.py security
```

### Test Results
The tests verify:
- Database initialization
- User registration with email verification
- User authentication and authorization
- JWT token handling and rotation
- Password management and reset flows
- Email sending and templates
- User management and RBAC
- Security features and rate limiting
- Feature configuration

## 🔐 Security Features

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

## 🔄 Module Reusability

### Copy to New Project
```bash
# 1. Copy auth module
cp -r src/features/auth/ new_project/src/features/auth/
cp -r src/shared/ new_project/src/shared/

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example new_project/.env

# 4. Integrate in main app
from features.auth import AuthModule, AuthConfig

auth = AuthModule(AuthConfig())
auth.setup(app)
```

### Benefits
- ✅ **Self-Contained**: All auth logic in one module
- ✅ **Zero Dependencies**: No external auth requirements  
- ✅ **Configuration-Driven**: Enable/disable features easily
- ✅ **Production-Ready**: Enterprise security features
- ✅ **Well-Tested**: Comprehensive test coverage

## 📁 File Structure

```
src/features/auth/
├── __init__.py                  # Module interface
├── config.py                   # Auth configuration  
├── auth_module.py              # Main module class
├── domain/
│   ├── entities.py             # AuthUser entity
│   ├── enums.py                # AuthRole, TokenType
│   └── events.py               # Domain events
├── application/
│   └── services/
│       ├── auth_service.py     # Core auth logic
│       ├── user_service.py     # User management
│       ├── email_verification_service.py
│       ├── password_reset_service.py
│       ├── account_lockout_service.py
│       ├── token_rotation_service.py
│       └── admin_setup_service.py
├── infrastructure/
│   ├── database/
│   │   ├── models.py           # SQLAlchemy models
│   │   └── repositories.py    # Data access
│   └── security/
│       ├── password_hasher.py  # Password utilities
│       ├── jwt_handler.py      # JWT utilities
│       └── token_generator.py  # Token generation
└── presentation/
    ├── api/
    │   ├── router.py           # FastAPI routes
    │   ├── schemas.py          # Request/response schemas
    │   └── dependencies.py    # Auth dependencies
    └── middleware/
        └── rate_limit_middleware.py
```

## 🎯 Next Steps

### Adding Features
1. Copy another feature module template
2. Implement domain, application, infrastructure layers
3. Create API endpoints
4. Integrate with main app

### Production Deployment
1. Use PostgreSQL database
2. Configure real email provider
3. Generate secure JWT secret
4. Set up HTTPS
5. Configure monitoring

## 🎉 Success!

The refactored auth module provides:
- **Clean Architecture**: Feature-based, modular design
- **Enterprise Security**: Production-ready auth features
- **Easy Reusability**: Copy-paste to new projects
- **Comprehensive Testing**: Verified functionality
- **Great Documentation**: Clear usage examples

**Your auth module is now ready for production and reuse!** 🚀