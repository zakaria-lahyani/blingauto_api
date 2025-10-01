# Authentication Feature Rules

## Business Rules

### RG-AUTH-001: Password Policy
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter  
- At least 1 number
- At least 1 special character

### RG-AUTH-002: Account Lockout
- Lock account after 5 failed login attempts
- Lockout duration: 30 minutes
- Reset attempts counter on successful login

### RG-AUTH-003: Session Management
- Access token expiry: 1 hour
- Refresh token expiry: 30 days
- Single active session per user (optional)

### RG-AUTH-004: Email Verification
- Email verification required for new accounts
- Verification token expiry: 24 hours
- Resend limit: 3 times per hour

### RG-AUTH-005: Password Reset
- Reset token expiry: 1 hour
- Single-use tokens only
- Rate limit: 3 requests per hour per email

### RG-AUTH-006: Role Management
- Users can have roles: client, washer, admin
- Role transitions require admin approval
- Cannot delete users with active bookings

## Technical Rules

### RG-AUTH-007: Security
- Passwords must be hashed using bcrypt
- JWTs must be signed with secure secret
- Sensitive data must not be logged

### RG-AUTH-008: Data Validation
- Email format validation required
- Phone number format validation (if applicable)
- Name fields: 2-50 characters each