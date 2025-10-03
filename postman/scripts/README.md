# Postman Testing Scripts

## 📁 Available Scripts

### Email Verification Helper

Automates the email verification process by querying the database for tokens and calling the API.

**Scripts:**
- `verify-email-docker.sh` - Linux/Mac bash script
- `verify-email-docker.bat` - Windows batch script

## 🚀 Quick Usage

### Linux/Mac

```bash
# Make executable
chmod +x verify-email-docker.sh

# Verify a user's email
./verify-email-docker.sh user@example.com
```

### Windows

```cmd
# Run directly
verify-email-docker.bat user@example.com
```

## 📋 What the Scripts Do

1. **Query Database**
   - Connects to Docker database container
   - Retrieves valid verification token for the email
   - Checks if token exists, is not used, and not expired

2. **Call API**
   - Makes POST request to `/api/v1/auth/verify-email`
   - Sends the verification token
   - Displays API response

3. **Verify Success**
   - Queries database to confirm `is_email_verified = true`
   - Shows verification timestamp
   - Displays success/failure status

## ⚙️ Configuration

### Environment Variables

**Linux/Mac:**
```bash
export API_URL=http://localhost:8000
export DB_CONTAINER=blingauto_api-db-1
```

**Windows:**
```cmd
set API_URL=http://localhost:8000
set DB_CONTAINER=blingauto_api-db-1
```

### Default Values

| Variable | Default | Description |
|----------|---------|-------------|
| `API_URL` | `http://localhost:8000` | API base URL |
| `DB_CONTAINER` | `blingauto_api-db-1` | Database container name |

## 📊 Example Output

### Success Case

```
================================================
   BlingAuto Email Verification Helper
================================================

→ Step 1: Retrieving verification token from database...
  Email: testuser@example.com
✓ Token found
  Token: a1b2c3d4-e5f6-7890...567890

→ Step 2: Calling verification API...
  URL: http://localhost:8000/api/v1/auth/verify-email

✓ Email verified successfully!

Response:
Email verified successfully. Your account is now active.

→ Step 3: Verifying database status...
           email            | is_email_verified |     email_verified_at
----------------------------+-------------------+---------------------------
 testuser@example.com       | t                 | 2025-10-03 14:23:45.123456

================================================
        Verification Complete! ✓
================================================
```

### Error Case - No Token Found

```
================================================
   BlingAuto Email Verification Helper
================================================

→ Step 1: Retrieving verification token from database...
  Email: nonexistent@example.com
✗ No valid verification token found

Possible reasons:
  - User hasn't registered yet
  - Token has already been used
  - Token has expired (24 hour expiration)
  - Email address is incorrect

→ Checking for any tokens for this email...
 token | created_at | expires_at | is_used | used_at
-------+------------+------------+---------+---------
(0 rows)
```

### Error Case - Token Expired

```
================================================
   BlingAuto Email Verification Helper
================================================

→ Step 1: Retrieving verification token from database...
  Email: expired@example.com
✗ No valid verification token found

→ Checking for any tokens for this email...
                 token                  |     created_at      |      expires_at     | is_used | used_at
----------------------------------------+---------------------+---------------------+---------+---------
 abc123-def456-789...                   | 2025-10-01 14:00:00 | 2025-10-02 14:00:00 | f       |
```

## 🔍 Troubleshooting

### Container Not Found

**Error:** `Error: No such container: blingauto_api-db-1`

**Solution:**
```bash
# List database containers
docker ps --filter "name=db"

# Set correct container name
export DB_CONTAINER=your_actual_container_name
```

### Database Connection Error

**Error:** `psql: FATAL: database "blingauto" does not exist`

**Solution:**
```bash
# List databases in container
docker exec -i blingauto_api-db-1 psql -U postgres -l

# Update database name in script if needed
```

### API Not Responding

**Error:** `curl: (7) Failed to connect to localhost port 8000`

**Solution:**
```bash
# Check if API is running
docker ps --filter "name=api"

# Check API logs
docker logs blingauto_api-api-1

# Set correct API URL
export API_URL=http://localhost:YOUR_PORT
```

### Permission Denied (Linux/Mac)

**Error:** `bash: ./verify-email-docker.sh: Permission denied`

**Solution:**
```bash
chmod +x verify-email-docker.sh
```

## 🧪 Integration with Tests

### Postman Collection

Use the script before running the verification tests:

```bash
# 1. Run registration test in Postman
# 2. Copy the email from environment variable
# 3. Run this script
./verify-email-docker.sh $(cat .env | grep verify_test_email | cut -d'=' -f2)

# 4. Continue with other tests
```

### CI/CD Pipeline

```yaml
# GitHub Actions
- name: Verify Test User
  run: |
    chmod +x postman/scripts/verify-email-docker.sh
    ./postman/scripts/verify-email-docker.sh testuser@example.com

# GitLab CI
verify_email:
  script:
    - chmod +x postman/scripts/verify-email-docker.sh
    - ./postman/scripts/verify-email-docker.sh testuser@example.com
```

## 📚 Related Documentation

- **[EMAIL_VERIFICATION_TESTING.md](../EMAIL_VERIFICATION_TESTING.md)** - Complete testing guide
- **[DOCKER_VERIFICATION_COMMANDS.md](../DOCKER_VERIFICATION_COMMANDS.md)** - All Docker commands
- **Collection:** `02-Complete-Authentication-Profile.postman_collection.json`

## 💡 Tips

1. **Batch Verification**
   ```bash
   # Verify multiple users
   for email in user1@test.com user2@test.com user3@test.com; do
     ./verify-email-docker.sh "$email"
   done
   ```

2. **Check Before Verifying**
   ```bash
   # Check if user needs verification
   docker exec -i blingauto_api-db-1 psql -U postgres -d blingauto -c \
     "SELECT email, is_email_verified FROM users WHERE email = 'user@test.com';"
   ```

3. **Log Output to File**
   ```bash
   # Save verification results
   ./verify-email-docker.sh user@test.com > verification-log.txt 2>&1
   ```

4. **Quiet Mode (just errors)**
   ```bash
   # Only show errors
   ./verify-email-docker.sh user@test.com 2>&1 | grep -E '(Error|✗|Failed)'
   ```

## 🎯 Use Cases

### Development
- Quickly verify test accounts without email setup
- Test verification flow end-to-end
- Debug verification issues

### Testing
- Automate email verification in test suites
- Verify multiple test users
- Integration testing with Postman/Newman

### Production Support
- Manually verify users when email service is down
- Troubleshoot verification issues
- Bulk verify users (emergency only)

---

**Created:** 2025-10-03
**Last Updated:** 2025-10-03
**Maintainer:** Development Team
