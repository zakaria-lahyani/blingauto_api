# Check and Verify Users Script
# This script checks if users are verified and verifies them if not

param(
    [string]$DbContainer = "blingauto-postgres",
    [string]$DbUser = "blingauto_user",
    [string]$DbName = "blingauto"
)

$emails = @("test1759495367950@example.com", "test1759495956402@example.com")

$ColorGreen = "Green"
$ColorYellow = "Yellow"
$ColorBlue = "Cyan"
$ColorRed = "Red"

Write-Host "================================================" -ForegroundColor $ColorBlue
Write-Host "   User Verification Checker & Fixer" -ForegroundColor $ColorBlue
Write-Host "================================================" -ForegroundColor $ColorBlue
Write-Host ""

# Check if container is running
Write-Host "Checking Docker container..." -ForegroundColor $ColorYellow
$containerCheck = docker ps --filter "name=$DbContainer" --format "{{.Names}}" 2>&1

if ($containerCheck -is [System.Management.Automation.ErrorRecord] -or [string]::IsNullOrWhiteSpace($containerCheck)) {
    Write-Host "[ERROR] Container '$DbContainer' not found or not running" -ForegroundColor $ColorRed
    Write-Host ""
    Write-Host "Available containers:" -ForegroundColor $ColorYellow
    docker ps --format "table {{.Names}}\t{{.Status}}"
    Write-Host ""
    Write-Host "Try running with the correct container name:" -ForegroundColor $ColorYellow
    Write-Host "  .\check-and-verify-users.ps1 -DbContainer YOUR_CONTAINER_NAME" -ForegroundColor Gray
    exit 1
}

Write-Host "[SUCCESS] Container '$DbContainer' is running" -ForegroundColor $ColorGreen
Write-Host ""

# Step 1: Check current status
Write-Host "[Step 1] Checking current verification status..." -ForegroundColor $ColorYellow
Write-Host ""

$emailList = ($emails | ForEach-Object { "'$_'" }) -join ','
$checkQuery = "SELECT email, is_email_verified, COALESCE(email_verified_at::text, 'NULL') as verified_at FROM users WHERE email IN ($emailList);"

Write-Host "Querying database..." -ForegroundColor Gray
$currentStatus = docker exec -i $DbContainer psql -U $DbUser -d $DbName -c $checkQuery 2>&1

if ($currentStatus -is [System.Management.Automation.ErrorRecord]) {
    Write-Host "[ERROR] Database query failed" -ForegroundColor $ColorRed
    Write-Host "  $($currentStatus.Exception.Message)" -ForegroundColor Gray
    exit 1
}

Write-Host $currentStatus
Write-Host ""

# Step 2: Count unverified users
$countQuery = "SELECT COUNT(*) FROM users WHERE email IN ($emailList) AND is_email_verified = FALSE;"
$unverifiedCount = docker exec -i $DbContainer psql -U $DbUser -d $DbName -t -A -c $countQuery 2>&1

if ($unverifiedCount -is [System.Management.Automation.ErrorRecord]) {
    $unverifiedCountNum = 2  # Assume both need verification
} else {
    $unverifiedCountStr = $unverifiedCount | Out-String
    $unverifiedCountNum = [int]$unverifiedCountStr.Trim()
}

if ($unverifiedCountNum -eq 0) {
    Write-Host "[SUCCESS] All users are already verified!" -ForegroundColor $ColorGreen
    Write-Host ""
    Write-Host "================================================" -ForegroundColor $ColorGreen
    Write-Host "     No Action Needed - Already Verified!" -ForegroundColor $ColorGreen
    Write-Host "================================================" -ForegroundColor $ColorGreen
    exit 0
}

Write-Host "[INFO] Found $unverifiedCountNum unverified user(s)" -ForegroundColor $ColorYellow
Write-Host ""

# Step 3: Verify the users
Write-Host "[Step 2] Verifying users in database..." -ForegroundColor $ColorYellow

$updateQuery = @"
UPDATE users
SET is_email_verified = TRUE,
    email_verified_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP
WHERE email IN ($emailList)
  AND is_email_verified = FALSE
RETURNING email, is_email_verified, email_verified_at;
"@

Write-Host "Executing UPDATE query..." -ForegroundColor Gray
$updateResult = docker exec -i $DbContainer psql -U $DbUser -d $DbName -c $updateQuery 2>&1

if ($updateResult -is [System.Management.Automation.ErrorRecord]) {
    Write-Host "[ERROR] Failed to update users" -ForegroundColor $ColorRed
    Write-Host "  $($updateResult.Exception.Message)" -ForegroundColor Gray
    exit 1
}

Write-Host $updateResult
Write-Host ""
Write-Host "[SUCCESS] Users updated in database" -ForegroundColor $ColorGreen
Write-Host ""

# Step 4: Mark verification tokens as used
Write-Host "[Step 3] Marking verification tokens as used..." -ForegroundColor $ColorYellow

$tokenUpdateQuery = @"
UPDATE email_verification_tokens
SET is_used = TRUE,
    used_at = CURRENT_TIMESTAMP
WHERE email IN ($emailList)
  AND is_used = FALSE;
"@

docker exec -i $DbContainer psql -U $DbUser -d $DbName -c $tokenUpdateQuery 2>&1 | Out-Null
Write-Host "[SUCCESS] Verification tokens marked as used" -ForegroundColor $ColorGreen
Write-Host ""

# Step 5: Final verification
Write-Host "[Step 4] Final verification check..." -ForegroundColor $ColorYellow
Write-Host ""

$finalQuery = @"
SELECT
    email,
    is_email_verified as verified,
    email_verified_at::timestamp(0) as verified_at,
    CASE
        WHEN is_email_verified THEN 'VERIFIED'
        ELSE 'NOT VERIFIED'
    END as status
FROM users
WHERE email IN ($emailList)
ORDER BY email;
"@

$finalStatus = docker exec -i $DbContainer psql -U $DbUser -d $DbName -c $finalQuery 2>&1
Write-Host $finalStatus
Write-Host ""

# Step 6: Verify all users are now verified
$verifyQuery = "SELECT COUNT(*) FROM users WHERE email IN ($emailList) AND is_email_verified = TRUE;"
$verifiedCount = docker exec -i $DbContainer psql -U $DbUser -d $DbName -t -A -c $verifyQuery 2>&1

if ($verifiedCount -is [System.Management.Automation.ErrorRecord]) {
    Write-Host "[WARNING] Could not verify final count" -ForegroundColor $ColorYellow
} else {
    $verifiedCountStr = $verifiedCount | Out-String
    $verifiedCountNum = [int]$verifiedCountStr.Trim()

    if ($verifiedCountNum -eq $emails.Count) {
        Write-Host "================================================" -ForegroundColor $ColorGreen
        Write-Host "     ALL USERS VERIFIED SUCCESSFULLY!" -ForegroundColor $ColorGreen
        Write-Host "     ($verifiedCountNum/$($emails.Count) users verified)" -ForegroundColor $ColorGreen
        Write-Host "================================================" -ForegroundColor $ColorGreen
        Write-Host ""
        Write-Host "Summary:" -ForegroundColor $ColorGreen
        foreach ($email in $emails) {
            Write-Host "  [OK] $email - VERIFIED" -ForegroundColor $ColorGreen
        }
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor $ColorYellow
        Write-Host "  - Users can now log in without email verification" -ForegroundColor Gray
        Write-Host "  - Test with: POST /api/v1/auth/login" -ForegroundColor Gray
    } else {
        Write-Host "================================================" -ForegroundColor $ColorYellow
        Write-Host "     PARTIAL VERIFICATION" -ForegroundColor $ColorYellow
        Write-Host "     ($verifiedCountNum/$($emails.Count) users verified)" -ForegroundColor $ColorYellow
        Write-Host "================================================" -ForegroundColor $ColorYellow
    }
}

Write-Host ""
Write-Host "Done!" -ForegroundColor $ColorBlue
