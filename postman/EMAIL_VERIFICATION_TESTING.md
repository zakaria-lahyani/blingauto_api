# Email Verification Testing Guide

## 📧 Overview

Email verification is a critical security feature that ensures users own the email address they register with. This guide explains how to test the email verification flow in the BlingAuto API.

## 🔄 Email Verification Flow

```
1. User Registers
   POST /api/v1/auth/register
   ↓
2. System Creates User (email_verified = false)
   ↓
3. System Generates Verification Token
   Stored in: email_verification_tokens table
   ↓
4. System Sends Email with Token
   Email contains: verification link or token
   ↓
5. User Clicks Link / Submits Token
   POST /api/v1/auth/verify-email
   ↓
6. System Validates Token
   ↓
7. System Marks User as Verified (email_verified = true)
   ↓
8. System Sends Welcome Email
```

## ✅ Tests Added (6 tests)

### 1. Registration Triggers Verification
**Test:** `Register User for Email Verification Test`
- **Endpoint:** `POST /api/v1/auth/register`
- **Purpose:** Verify registration succeeds and mentions email verification
- **Assertions:**
  - Status: 201 Created
  - Response contains `user_id`
  - Response contains `message` mentioning "verify"
  - Message mentions "email"

### 2. Informational Note
**Test:** `NOTE: Email Verification Token Flow`
- **Purpose:** Document that tokens are sent via email, not returned in API
- **Note:** In production, users receive email with verification link

### 3. Valid Token Verification
**Test:** `Verify Email - Valid Token (200)`
- **Endpoint:** `POST /api/v1/auth/verify-email`
- **Body:** `{ "token": "actual_verification_token" }`
- **Expected:** 200 OK
- **Note:** Requires real token from database (see "How to Get Tokens" below)

### 4. Invalid Token Rejection
**Test:** `Verify Email - Invalid Token (404)`
- **Endpoint:** `POST /api/v1/auth/verify-email`
- **Body:** `{ "token": "invalid_token_12345" }`
- **Expected:** 404 Not Found

### 5. Empty Token Rejection
**Test:** `Verify Email - Empty Token (422)`
- **Endpoint:** `POST /api/v1/auth/verify-email`
- **Body:** `{ "token": "" }`
- **Expected:** 422 Unprocessable Entity

### 6. Missing Token Field
**Test:** `Verify Email - Missing Token Field (422)`
- **Endpoint:** `POST /api/v1/auth/verify-email`
- **Body:** `{}`
- **Expected:** 422 Unprocessable Entity

## 🔑 How to Get Verification Tokens for Testing

### Option 0: Automated Docker Script (⭐ EASIEST - Recommended)

**Complete automation - just provide the email address!**

**Linux/Mac:**
```bash
chmod +x postman/scripts/verify-email-docker.sh
./postman/scripts/verify-email-docker.sh verifytest123456@example.com
```

**Windows:**
```cmd
postman\scripts\verify-email-docker.bat verifytest123456@example.com
```

**What it does:**
1. ✅ Queries database for valid verification token
2. ✅ Calls API to verify email
3. ✅ Confirms verification in database
4. ✅ Shows success/failure with detailed output

**Example output:**
```
================================================
   BlingAuto Email Verification Helper
================================================

→ Step 1: Retrieving verification token from database...
  Email: verifytest123456@example.com
✓ Token found
  Token: a1b2c3d4-e5f6-7890...567890

→ Step 2: Calling verification API...
  URL: http://localhost:8000/api/v1/auth/verify-email

✓ Email verified successfully!

Response:
Email verified successfully. Your account is now active.

→ Step 3: Verifying database status...
           email            | is_email_verified | email_verified_at
----------------------------+-------------------+-------------------
 verifytest123456@...       | t                 | 2025-10-03 14:23:45

================================================
        Verification Complete! ✓
================================================
```

**📚 For more Docker commands:** See [DOCKER_VERIFICATION_COMMANDS.md](DOCKER_VERIFICATION_COMMANDS.md)

### Option 1: Query Database Manually

```sql
-- Get the most recent verification token for a user
SELECT token, email, created_at, is_used, expires_at
FROM email_verification_tokens
WHERE email = 'verifytest123456@example.com'
ORDER BY created_at DESC
LIMIT 1;
```

**Steps:**
1. Run the test `Register User for Email Verification Test`
2. Note the email address from environment: `verify_test_email`
3. Query database with that email
4. Copy the `token` value
5. Set it in Postman environment: `test_verification_token`
6. Re-run the `Verify Email - Valid Token` test

### Option 2: Mock Email Service (For Automated Testing)

Create a test email service that captures tokens instead of sending emails:

```python
# tests/mocks/email_service.py
class MockEmailService:
    def __init__(self):
        self.sent_emails = []
        self.verification_tokens = {}

    async def send_verification_email(self, email: str, token: str):
        self.verification_tokens[email] = token
        self.sent_emails.append({
            'to': email,
            'type': 'verification',
            'token': token
        })

    def get_verification_token(self, email: str) -> str:
        return self.verification_tokens.get(email)
```

### Option 3: Test Email Service (MailHog/MailTrap)

Use a test email service that captures emails:

**MailHog:**
```yaml
# docker-compose.yml
services:
  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI
```

**Access emails:**
- Web UI: http://localhost:8025
- API: http://localhost:8025/api/v2/messages

**Automated token extraction:**
```javascript
// Postman pre-request script
const mailhogUrl = 'http://localhost:8025/api/v2/messages';

pm.sendRequest(mailhogUrl, (err, response) => {
    if (!err) {
        const messages = response.json().items;
        const email = pm.environment.get('verify_test_email');

        // Find verification email for this user
        const verificationEmail = messages.find(m =>
            m.To[0].Mailbox + '@' + m.To[0].Domain === email
        );

        if (verificationEmail) {
            // Extract token from email body
            const body = verificationEmail.Content.Body;
            const tokenMatch = body.match(/token=([a-zA-Z0-9-_]+)/);

            if (tokenMatch) {
                pm.environment.set('test_verification_token', tokenMatch[1]);
            }
        }
    }
});
```

## 📋 Database Schema

### `email_verification_tokens` table

```sql
CREATE TABLE email_verification_tokens (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    email VARCHAR(255) NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP
);
```

**Key Fields:**
- `token` - Unique verification token (UUID-based)
- `expires_at` - Token expiration (typically 24 hours)
- `is_used` - Whether token has been consumed
- `used_at` - When token was used

## 🧪 Testing Scenarios

### Scenario 1: Happy Path (Manual Test)

```bash
# 1. Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User"
  }'

# Response:
# {
#   "user_id": "uuid-here",
#   "email": "test@example.com",
#   "message": "Registration successful. Please check your email..."
# }

# 2. Get token from database
psql -d blingauto -c "
  SELECT token FROM email_verification_tokens
  WHERE email = 'test@example.com'
  ORDER BY created_at DESC LIMIT 1;
"

# 3. Verify email
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{
    "token": "token-from-database"
  }'

# Response:
# {
#   "message": "Email verified successfully. Your account is now active."
# }
```

### Scenario 2: Expired Token

```sql
-- Manually expire a token for testing
UPDATE email_verification_tokens
SET expires_at = NOW() - INTERVAL '1 hour'
WHERE email = 'test@example.com';
```

**Expected:** 400 Bad Request - "Verification token is expired"

### Scenario 3: Already Used Token

```sql
-- Mark token as used
UPDATE email_verification_tokens
SET is_used = TRUE, used_at = NOW()
WHERE email = 'test@example.com';
```

**Expected:** 400 Bad Request - "Verification token is expired or already used"

### Scenario 4: Token for Different User

**Expected:** 404 Not Found - Token doesn't exist for that user

## 🔍 Checking Verification Status

### Via Profile Endpoint

```bash
# Get user profile (requires auth token)
curl http://localhost:8000/api/v1/auth/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response includes:**
```json
{
  "user_id": "uuid",
  "email": "test@example.com",
  "email_verified": true,  // ← Verification status
  "email_verified_at": "2025-10-03T12:34:56Z"
}
```

### Via Admin User Endpoint

```bash
# Admin can check any user's status
curl http://localhost:8000/api/v1/auth/users/{user_id} \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## 🚀 Running the Tests

### In Postman UI

1. Import collection: `02-Complete-Authentication-Profile.postman_collection.json`
2. Select environment: `BlingAuto-Local`
3. Navigate to folder: `Email Verification Flow`
4. Run folder

**For valid token test:**
1. Run: `Register User for Email Verification Test`
2. Query database for token (see SQL above)
3. Set `test_verification_token` in environment
4. Run: `Verify Email - Valid Token`

### With Newman CLI

```bash
# Run email verification tests only
newman run collections/02-Complete-Authentication-Profile.postman_collection.json \
  -e environments/BlingAuto-Local.postman_environment.json \
  --folder "Email Verification Flow"
```

## 📊 Test Matrix

| Test Case | Endpoint | Body | Expected Status | Validation |
|-----------|----------|------|-----------------|------------|
| Register triggers email | `/register` | Valid user data | 201 | Message mentions verification |
| Valid token | `/verify-email` | `{"token": "valid"}` | 200 | Email verified successfully |
| Invalid token | `/verify-email` | `{"token": "invalid"}` | 404 | Token not found |
| Expired token | `/verify-email` | `{"token": "expired"}` | 400 | Token expired |
| Used token | `/verify-email` | `{"token": "used"}` | 400 | Already used |
| Empty token | `/verify-email` | `{"token": ""}` | 422 | Validation error |
| Missing field | `/verify-email` | `{}` | 422 | Field required |

## 🛠️ Troubleshooting

### Issue: "Token not found" for valid token

**Causes:**
- Token hasn't been created yet (async email sending)
- Wrong email queried in database
- Token expired (24 hour default)
- Token already used

**Solution:**
```sql
-- Check if token exists
SELECT token, email, expires_at, is_used
FROM email_verification_tokens
WHERE email = 'YOUR_EMAIL'
ORDER BY created_at DESC;
```

### Issue: Emails not being sent

**Causes:**
- Email service not configured
- SMTP credentials missing
- Email service down

**Solution:**
- Check email service logs
- Verify SMTP configuration in `.env`
- Use mock email service for testing

### Issue: Cannot automate tests with valid token

**Solution:**
Use one of these approaches:
1. **Database query in pre-request script** (if Postman can access DB)
2. **Mock email service** (recommended for CI/CD)
3. **MailHog/MailTrap** with API integration
4. **Manual token insertion** for one-time verification

## 💡 Best Practices

1. **Never return tokens in API responses**
   - Security risk: tokens should only be in emails
   - Current implementation ✅ tokens sent via email only

2. **Use test email services in development**
   - MailHog for local development
   - MailTrap for staging environments
   - Real SMTP for production

3. **Token expiration**
   - Default: 24 hours
   - Balance security vs user experience
   - Allow resending if expired

4. **One-time use tokens**
   - Mark as used after verification
   - Prevent replay attacks

5. **Rate limiting**
   - Limit verification attempts
   - Prevent brute force token guessing

## 📝 Future Enhancements

### Resend Verification Email

```bash
POST /api/v1/auth/resend-verification
{
  "email": "user@example.com"
}
```

**Implementation:**
- Invalidate old tokens
- Generate new token
- Send new email
- Rate limit: max 3 requests per hour

### Check Verification Status Without Auth

```bash
GET /api/v1/auth/verification-status?email=user@example.com
```

**Response:**
```json
{
  "email_verified": false,
  "can_resend": true,
  "next_resend_at": "2025-10-03T13:00:00Z"
}
```

## 📚 Related Documentation

- **Registration Flow:** See `02-Complete-Authentication-Profile` collection
- **Email Service:** `app/features/auth/adapters/services.py`
- **Verification Use Case:** `app/features/auth/use_cases/verify_email.py`
- **Token Repository:** `app/features/auth/adapters/repositories.py`

---

**Created:** 2025-10-03
**Tests Added:** 6
**New Total:** 337 tests (was 331)
**Collection:** 02-Complete-Authentication-Profile (47 → 53 tests)
