# Docker Commands for Email Verification

## 🚀 Quick Start - One-Line Commands

### Verify Email (Automatic)

**Linux/Mac:**
```bash
./postman/scripts/verify-email-docker.sh verifytest123456@example.com
```

**Windows:**
```cmd
postman\scripts\verify-email-docker.bat verifytest123456@example.com
```

## 📋 Manual Step-by-Step Commands

### Step 1: Get Verification Token from Database

```bash
docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -t -A -c \
  "SELECT token FROM email_verification_tokens
   WHERE email = 'YOUR_EMAIL_HERE'
     AND is_used = FALSE
     AND expires_at > NOW()
   ORDER BY created_at DESC
   LIMIT 1;"
```

**Example:**
```bash
docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -t -A -c \
  "SELECT token FROM email_verification_tokens
   WHERE email = 'verifytest1696348800@example.com'
     AND is_used = FALSE
     AND expires_at > NOW()
   ORDER BY created_at DESC
   LIMIT 1;"
```

**Output:**
```
a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Step 2: Verify Email via API

```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "TOKEN_FROM_STEP_1"}'
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}'
```

**Success Response (200):**
```json
{
  "message": "Email verified successfully. Your account is now active."
}
```

### Step 3: Verify in Database

```bash
docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -c \
  "SELECT email, is_email_verified, email_verified_at
   FROM users
   WHERE email = 'YOUR_EMAIL_HERE';"
```

**Output:**
```
           email            | is_email_verified |     email_verified_at
----------------------------+-------------------+---------------------------
 verifytest@example.com     | t                 | 2025-10-03 14:23:45.123456
```

## 🔄 Combined One-Liner (Advanced)

### Linux/Mac (with jq)

```bash
EMAIL="verifytest123456@example.com" && \
TOKEN=$(docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -t -A -c \
  "SELECT token FROM email_verification_tokens WHERE email = '$EMAIL' AND is_used = FALSE AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1;") && \
echo "Token: $TOKEN" && \
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d "{\"token\": \"$TOKEN\"}" | jq '.'
```

### Windows PowerShell

```powershell
$EMAIL = "verifytest123456@example.com"
$TOKEN = docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -t -A -c "SELECT token FROM email_verification_tokens WHERE email = '$EMAIL' AND is_used = FALSE AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1;"
Write-Host "Token: $TOKEN"
curl.exe -X POST http://localhost:8000/api/v1/auth/verify-email `
  -H "Content-Type: application/json" `
  -d "{`"token`": `"$TOKEN`"}"
```

## 📊 Useful Database Queries

### Check All Verification Tokens for a User

```bash
docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -c \
  "SELECT
     token,
     email,
     created_at,
     expires_at,
     is_used,
     used_at,
     CASE
       WHEN is_used THEN 'Used'
       WHEN expires_at < NOW() THEN 'Expired'
       ELSE 'Valid'
     END AS status
   FROM email_verification_tokens
   WHERE email = 'YOUR_EMAIL_HERE'
   ORDER BY created_at DESC;"
```

### Check User Verification Status

```bash
docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -c \
  "SELECT
     id,
     email,
     first_name,
     last_name,
     role,
     is_email_verified,
     email_verified_at,
     created_at
   FROM users
   WHERE email = 'YOUR_EMAIL_HERE';"
```

### List All Unverified Users

```bash
docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -c \
  "SELECT
     email,
     first_name,
     last_name,
     created_at,
     EXTRACT(EPOCH FROM (NOW() - created_at))/3600 AS hours_since_registration
   FROM users
   WHERE is_email_verified = FALSE
   ORDER BY created_at DESC;"
```

### List Valid Tokens Waiting for Verification

```bash
docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -c \
  "SELECT
     email,
     created_at,
     expires_at,
     EXTRACT(EPOCH FROM (expires_at - NOW()))/3600 AS hours_until_expiry
   FROM email_verification_tokens
   WHERE is_used = FALSE
     AND expires_at > NOW()
   ORDER BY created_at DESC;"
```

## 🧪 Testing Scenarios

### Scenario 1: Fresh Registration → Verify

```bash
# 1. Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "first_name": "New",
    "last_name": "User"
  }'

# 2. Wait a moment for async email sending
sleep 2

# 3. Get token and verify (one command)
docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -t -A -c \
  "SELECT token FROM email_verification_tokens WHERE email = 'newuser@example.com' ORDER BY created_at DESC LIMIT 1;" | \
  xargs -I {} curl -X POST http://localhost:8000/api/v1/auth/verify-email \
    -H "Content-Type: application/json" \
    -d '{"token": "{}"}'
```

### Scenario 2: Manually Expire Token (Testing)

```bash
# Expire the token
docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -c \
  "UPDATE email_verification_tokens
   SET expires_at = NOW() - INTERVAL '1 hour'
   WHERE email = 'test@example.com'
     AND is_used = FALSE;"

# Try to verify (should fail with 400)
TOKEN=$(docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -t -A -c \
  "SELECT token FROM email_verification_tokens WHERE email = 'test@example.com' ORDER BY created_at DESC LIMIT 1;")

curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d "{\"token\": \"$TOKEN\"}"
```

**Expected:** 400 Bad Request - "Verification token is expired or already used"

### Scenario 3: Manually Mark as Used (Testing)

```bash
# Mark token as used
docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -c \
  "UPDATE email_verification_tokens
   SET is_used = TRUE, used_at = NOW()
   WHERE email = 'test@example.com'
     AND is_used = FALSE;"

# Try to verify (should fail)
TOKEN=$(docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -t -A -c \
  "SELECT token FROM email_verification_tokens WHERE email = 'test@example.com' ORDER BY created_at DESC LIMIT 1;")

curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d "{\"token\": \"$TOKEN\"}"
```

**Expected:** 400 Bad Request - "Verification token is expired or already used"

### Scenario 4: Verify Multiple Users (Bulk)

```bash
# Get all unverified users with valid tokens
docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -t -A -F'|' -c \
  "SELECT DISTINCT evt.email, evt.token
   FROM email_verification_tokens evt
   JOIN users u ON evt.email = u.email
   WHERE evt.is_used = FALSE
     AND evt.expires_at > NOW()
     AND u.is_email_verified = FALSE;" | \
while IFS='|' read -r email token; do
  echo "Verifying: $email"
  curl -s -X POST http://localhost:8000/api/v1/auth/verify-email \
    -H "Content-Type: application/json" \
    -d "{\"token\": \"$token\"}" | jq -r '.message'
  echo "---"
done
```

## 🔧 Troubleshooting

### Issue: "No valid verification token found"

**Check if token exists:**
```bash
docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -c \
  "SELECT * FROM email_verification_tokens WHERE email = 'YOUR_EMAIL';"
```

**Possible fixes:**
- User hasn't registered → Check users table
- Token expired → Generate new token
- Token already used → Check `is_used` column

### Issue: "Database container not found"

**List running containers:**
```bash
docker ps --filter "name=db"
```

**Common container names:**
- `blingauto_api-db-1`
- `api-db-1`
- `lavage-db-1`

**Use correct name:**
```bash
export DB_CONTAINER=your_actual_container_name
```

### Issue: "psql: FATAL: database does not exist"

**List databases:**
```bash
docker exec -i blingauto_api-db-1 psql -U postgres -l
```

**Common database names:**
- `blingauto`
- `lavage`
- `car_wash`

### Issue: "curl command not found"

**Install curl:**
```bash
# Ubuntu/Debian
sudo apt-get install curl

# macOS
brew install curl

# Windows
# curl.exe is built into Windows 10+
```

## 📝 Environment Variables

Set these to customize the scripts:

```bash
# Linux/Mac
export API_URL=http://localhost:8000
export DB_CONTAINER=blingauto_api-db-1
export DB_USER=postgres
export DB_NAME=blingauto

# Windows
set API_URL=http://localhost:8000
set DB_CONTAINER=blingauto_api-db-1
set DB_USER=postgres
set DB_NAME=blingauto
```

## 🎯 Postman Integration

### Pre-request Script (Get Token from Database)

```javascript
// This requires Newman CLI with database access
// Or use the Docker scripts externally

const exec = require('child_process').exec;
const email = pm.environment.get('verify_test_email');

exec(`docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -t -A -c "SELECT token FROM email_verification_tokens WHERE email = '${email}' AND is_used = FALSE AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1;"`,
    (error, stdout, stderr) => {
        if (error) {
            console.error('Error getting token:', error);
            return;
        }

        const token = stdout.trim();
        pm.environment.set('test_verification_token', token);
        console.log('Token retrieved:', token);
    }
);
```

**Note:** This requires Newman to have access to Docker commands, which is typically only available in local development.

## 📚 Related Files

- **Bash Script:** `postman/scripts/verify-email-docker.sh`
- **Windows Script:** `postman/scripts/verify-email-docker.bat`
- **Testing Guide:** `postman/EMAIL_VERIFICATION_TESTING.md`
- **Collection:** `postman/collections/02-Complete-Authentication-Profile.postman_collection.json`

## 🚀 CI/CD Integration

### GitHub Actions Example

```yaml
- name: Verify Test User Email
  run: |
    chmod +x postman/scripts/verify-email-docker.sh
    ./postman/scripts/verify-email-docker.sh testuser@example.com
```

### GitLab CI Example

```yaml
verify_email:
  script:
    - chmod +x postman/scripts/verify-email-docker.sh
    - ./postman/scripts/verify-email-docker.sh testuser@example.com
```

---

**Created:** 2025-10-03
**Author:** Claude Code
**Purpose:** Simplify email verification testing in Docker environments
