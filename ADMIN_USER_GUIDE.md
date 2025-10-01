# BlingAuto API - Admin User Setup Guide

**Automatic Admin User Creation on Startup**

---

## Overview

The BlingAuto API supports automatic creation of an initial admin user during the first startup. This is useful for:

- **Production deployments**: Create admin access without manual database operations
- **Development environments**: Quick setup with default admin credentials
- **Docker deployments**: Fully automated initialization

---

## Configuration

### Environment Variables

Add these variables to your `.env` file or docker-compose environment:

```bash
# Initial Admin User (Optional)
INITIAL_ADMIN_EMAIL=admin@yourdomain.com
INITIAL_ADMIN_PASSWORD=ChangeThisSecurePassword123!
INITIAL_ADMIN_FIRST_NAME=Admin
INITIAL_ADMIN_LAST_NAME=User
```

### Variable Details

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `INITIAL_ADMIN_EMAIL` | Yes* | None | Admin email address (must be valid email) |
| `INITIAL_ADMIN_PASSWORD` | Yes* | None | Admin password (minimum 8 characters) |
| `INITIAL_ADMIN_FIRST_NAME` | No | "Admin" | Admin first name |
| `INITIAL_ADMIN_LAST_NAME` | No | "User" | Admin last name |

\* Both `INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD` must be set for admin user creation to proceed.

---

## How It Works

### Automatic Creation Process

1. **On Startup**: After database migrations complete, the admin creation script runs
2. **Check Existing**: Script checks if a user with the specified email already exists
3. **Create if Needed**: If no user exists, creates new admin with:
   - Role: `ADMIN`
   - Status: `ACTIVE` (bypasses email verification)
   - Email Verified: `true`
   - All admin permissions enabled
4. **Skip if Exists**: If user already exists, logs message and continues

### Startup Log Output

**When creating new admin**:
```
==============================================================================
Creating Default Admin User
==============================================================================

Creating new admin user: admin@blingauto.com

✓ Admin user created successfully!
  User ID: 550e8400-e29b-41d4-a716-446655440000
  Email: admin@blingauto.com
  Name: Admin User
  Role: admin
  Status: active
  Email Verified: True

⚠️  IMPORTANT: Change the admin password after first login!

==============================================================================
Admin User Setup Complete
==============================================================================
```

**When admin already exists**:
```
==============================================================================
Creating Default Admin User
==============================================================================

✓ Admin user already exists: admin@blingauto.com
  User ID: 550e8400-e29b-41d4-a716-446655440000
  Role: admin
  Status: active

==============================================================================
Admin User Setup Complete
==============================================================================
```

**When credentials not configured**:
```
⚠️  Admin credentials not configured
   Set INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_PASSWORD environment variables
   to create a default admin user on startup.
```

---

## Usage Examples

### Docker Compose

Add to your `docker-compose.yml` or `.env` file:

```yaml
api:
  environment:
    INITIAL_ADMIN_EMAIL: admin@blingauto.com
    INITIAL_ADMIN_PASSWORD: MySecurePassword123!
    INITIAL_ADMIN_FIRST_NAME: System
    INITIAL_ADMIN_LAST_NAME: Administrator
```

Or in `.env`:
```bash
INITIAL_ADMIN_EMAIL=admin@blingauto.com
INITIAL_ADMIN_PASSWORD=MySecurePassword123!
INITIAL_ADMIN_FIRST_NAME=System
INITIAL_ADMIN_LAST_NAME=Administrator
```

### Manual Script Execution

You can also run the script manually:

```bash
# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/blingauto"
export INITIAL_ADMIN_EMAIL="admin@blingauto.com"
export INITIAL_ADMIN_PASSWORD="MySecurePassword123!"

# Run script
python scripts/create_admin.py
```

### Kubernetes Deployment

Use secrets for production:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: admin-credentials
type: Opaque
stringData:
  admin-email: admin@blingauto.com
  admin-password: MySecurePassword123!

---
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: api
        env:
        - name: INITIAL_ADMIN_EMAIL
          valueFrom:
            secretKeyRef:
              name: admin-credentials
              key: admin-email
        - name: INITIAL_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: admin-credentials
              key: admin-password
```

---

## Security Best Practices

### ⚠️ Production Security

1. **Use Strong Passwords**
   ```bash
   # Generate secure password
   python -c "import secrets; print(secrets.token_urlsafe(32))"

   # Use in .env
   INITIAL_ADMIN_PASSWORD=<generated-password>
   ```

2. **Change Password After First Login**
   - The initial password is temporary
   - Change it immediately via API or UI
   - Use password manager for permanent password

3. **Protect Environment Variables**
   - Never commit `.env` to version control
   - Use secrets management (AWS Secrets Manager, HashiCorp Vault)
   - Restrict access to environment configuration

4. **Rotate Credentials Regularly**
   - Change admin password every 90 days
   - Use strong, unique passwords
   - Enable MFA if available

### Password Requirements

- **Minimum Length**: 8 characters (12+ recommended for admin)
- **Complexity**: Use mix of uppercase, lowercase, numbers, symbols
- **No Common Patterns**: Avoid "password123", "admin", etc.
- **Unique**: Don't reuse passwords from other systems

**Good Examples**:
```bash
MyS3cure!PaSsw0rd2025
Admin#BlingAuto$2025!
C0mpl3x&SecureP@ssw0rd
```

**Bad Examples**:
```bash
password123
admin
12345678
blingauto
```

---

## Login as Admin

Once the admin user is created, you can login via the API:

### 1. Login Request

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@blingauto.com",
    "password": "your-admin-password"
  }'
```

### 2. Login Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@blingauto.com",
    "first_name": "Admin",
    "last_name": "User",
    "full_name": "Admin User",
    "role": "admin",
    "status": "active",
    "email_verified": true,
    "created_at": "2025-10-01T12:00:00Z"
  }
}
```

### 3. Use Access Token

Include the token in subsequent requests:

```bash
curl -X GET http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Change Admin Password

### Via API

```bash
# Get current user profile
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access-token>"

# Change password
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "old-password",
    "new_password": "new-secure-password",
    "confirm_password": "new-secure-password"
  }'
```

### Response

```json
{
  "message": "Password changed successfully",
  "password_changed_at": "2025-10-01T12:30:00Z"
}
```

---

## Troubleshooting

### Admin User Not Created

**Symptoms**: No admin user after startup, no error messages

**Causes**:
1. Environment variables not set
2. Environment variables have incorrect names
3. Database connection failed before admin creation

**Solutions**:
```bash
# 1. Check environment variables are set
docker-compose exec api env | grep INITIAL_ADMIN

# 2. Check startup logs
docker-compose logs api | grep -A 20 "Creating Default Admin User"

# 3. Run script manually
docker-compose exec api python scripts/create_admin.py

# 4. Check database for existing user
docker-compose exec postgres psql -U blingauto_user -d blingauto \
  -c "SELECT id, email, role, status FROM users WHERE email = 'admin@blingauto.com';"
```

### Admin Creation Failed

**Symptoms**: Error messages during startup

**Common Errors**:

1. **Invalid Email Format**
   ```
   Error: Invalid email format
   ```
   Solution: Use valid email format (e.g., `admin@blingauto.com`)

2. **Weak Password**
   ```
   Error: Password must be at least 8 characters
   ```
   Solution: Use password with minimum 8 characters

3. **Database Connection Error**
   ```
   Error: could not translate host name "postgres" to address
   ```
   Solution: Ensure PostgreSQL is running and accessible

4. **Table Does Not Exist**
   ```
   Error: relation "users" does not exist
   ```
   Solution: Run migrations first: `alembic upgrade head`

### Login Fails

**Symptoms**: 401 Unauthorized when trying to login

**Causes**:
1. Incorrect password
2. Email case mismatch (emails are case-insensitive)
3. Account locked due to failed attempts
4. Wrong environment

**Solutions**:
```bash
# 1. Check user exists and is active
docker-compose exec postgres psql -U blingauto_user -d blingauto \
  -c "SELECT id, email, role, status, failed_login_attempts, locked_until FROM users WHERE email = 'admin@blingauto.com';"

# 2. Reset failed login attempts
docker-compose exec postgres psql -U blingauto_user -d blingauto \
  -c "UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE email = 'admin@blingauto.com';"

# 3. Verify password by recreating user (WARNING: only in development)
docker-compose exec api python scripts/create_admin.py
```

---

## Disable Admin Auto-Creation

To disable automatic admin user creation:

1. **Remove or comment out environment variables**:
   ```bash
   # INITIAL_ADMIN_EMAIL=admin@blingauto.com
   # INITIAL_ADMIN_PASSWORD=MySecurePassword123!
   ```

2. **Or set to empty values**:
   ```bash
   INITIAL_ADMIN_EMAIL=
   INITIAL_ADMIN_PASSWORD=
   ```

3. **Restart services**:
   ```bash
   docker-compose restart api
   ```

---

## Script Location

The admin creation script is located at:
```
scripts/create_admin.py
```

You can modify this script to customize admin user creation behavior.

---

## FAQ

**Q: Can I create multiple admin users on startup?**
A: No, the script creates only one admin user. Create additional admins via API after initial setup.

**Q: What happens if I change the admin email in environment variables?**
A: The script checks for existing users by email. If you change the email, a new admin will be created with the new email.

**Q: Can I skip email verification for admin?**
A: Yes, admin users automatically have `email_verified=true` and `status=active`.

**Q: Is the admin password stored securely?**
A: Yes, passwords are hashed using bcrypt before storage. The plain text password is never stored.

**Q: Can I use this in production?**
A: Yes, but ensure you:
- Use strong passwords
- Change password after first login
- Store credentials in secrets management system
- Enable proper logging and monitoring

**Q: What if I forget the admin password?**
A: You'll need to reset it via direct database access or create a password reset flow.

---

## Support

For issues or questions:
- Check logs: `docker-compose logs api`
- Run script manually: `python scripts/create_admin.py`
- Review database: Check `users` table
- Contact: support@blingauto.com

---

**Last Updated**: 2025-10-01
**Script Version**: 1.0.0
