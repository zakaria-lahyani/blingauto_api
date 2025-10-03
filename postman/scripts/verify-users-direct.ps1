# Direct User Email Verification Script
# This script directly updates the database to mark users as verified
# Use this when you need to quickly verify test users without the email flow

param(
    [Parameter(Mandatory=$false)]
    [string[]]$Emails = @("test1759495367950@example.com", "test1759495956402@example.com"),

    [string]$DbContainer = "blingauto-postgres"
)

$ColorGreen = "Green"
$ColorYellow = "Yellow"
$ColorBlue = "Cyan"
$ColorRed = "Red"

Write-Host "================================================" -ForegroundColor $ColorBlue
Write-Host "   Direct Email Verification Tool" -ForegroundColor $ColorBlue
Write-Host "================================================" -ForegroundColor $ColorBlue
Write-Host ""

Write-Host "Users to verify:" -ForegroundColor $ColorYellow
foreach ($email in $Emails) {
    Write-Host "  - $email" -ForegroundColor Gray
}
Write-Host ""

# Step 1: Check current status
Write-Host "[Step 1] Checking current verification status..." -ForegroundColor $ColorYellow
$emailList = ($Emails | ForEach-Object { "'$_'" }) -join ','
$checkQuery = "SELECT email, is_email_verified, email_verified_at FROM users WHERE email IN ($emailList);"

Write-Host "Current status:" -ForegroundColor Gray
docker exec -i $DbContainer psql -U postgres -d blingauto -c $checkQuery
Write-Host ""

# Step 2: Verify the users
Write-Host "[Step 2] Marking users as verified..." -ForegroundColor $ColorYellow

$updateQuery = @"
UPDATE users
SET is_email_verified = TRUE,
    email_verified_at = NOW(),
    updated_at = NOW()
WHERE email IN ($emailList)
  AND is_email_verified = FALSE;
"@

$result = docker exec -i $DbContainer psql -U postgres -d blingauto -t -A -c $updateQuery 2>&1

if ($result -is [System.Management.Automation.ErrorRecord]) {
    Write-Host "[ERROR] Failed to update database" -ForegroundColor $ColorRed
    Write-Host "  $($result.Exception.Message)" -ForegroundColor Gray
    exit 1
}

$resultStr = $result | Out-String
$resultStr = $resultStr.Trim()

if ($resultStr -match "UPDATE (\d+)") {
    $count = $Matches[1]
    Write-Host "[SUCCESS] Updated $count user(s)" -ForegroundColor $ColorGreen
} else {
    Write-Host "[INFO] No users needed verification (already verified)" -ForegroundColor $ColorYellow
}
Write-Host ""

# Step 3: Mark verification tokens as used
Write-Host "[Step 3] Marking verification tokens as used..." -ForegroundColor $ColorYellow

$tokenUpdateQuery = @"
UPDATE email_verification_tokens
SET is_used = TRUE,
    used_at = NOW()
WHERE email IN ($emailList)
  AND is_used = FALSE;
"@

docker exec -i $DbContainer psql -U postgres -d blingauto -c $tokenUpdateQuery | Out-Null
Write-Host "[SUCCESS] Tokens marked as used" -ForegroundColor $ColorGreen
Write-Host ""

# Step 4: Verify final status
Write-Host "[Step 4] Verifying final status..." -ForegroundColor $ColorYellow
Write-Host "Final status:" -ForegroundColor Gray
docker exec -i $DbContainer psql -U postgres -d blingauto -c $checkQuery
Write-Host ""

Write-Host "================================================" -ForegroundColor $ColorGreen
Write-Host "     Verification Complete!" -ForegroundColor $ColorGreen
Write-Host "================================================" -ForegroundColor $ColorGreen
Write-Host ""
Write-Host "Next steps:" -ForegroundColor $ColorYellow
Write-Host "  - Users can now log in normally" -ForegroundColor Gray
Write-Host "  - Email verification is bypassed" -ForegroundColor Gray
Write-Host "  - Tokens are marked as used" -ForegroundColor Gray
