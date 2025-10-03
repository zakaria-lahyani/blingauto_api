# BlingAuto Email Verification Helper Script (PowerShell)
# Usage: .\verify-email-docker.ps1 email@example.com

param(
    [Parameter(Mandatory=$true)]
    [string]$Email,

    [string]$ApiUrl = "http://localhost:8000",
    [string]$DbContainer = "blingauto-postgres",
    [string]$DbUser = "blingauto_user",
    [string]$DbName = "blingauto"
)

# Colors
$ColorRed = "Red"
$ColorGreen = "Green"
$ColorYellow = "Yellow"
$ColorBlue = "Cyan"

Write-Host "================================================" -ForegroundColor $ColorBlue
Write-Host "   BlingAuto Email Verification Helper" -ForegroundColor $ColorBlue
Write-Host "================================================" -ForegroundColor $ColorBlue
Write-Host ""

# Step 1: Get verification token from database
Write-Host "[Step 1] Retrieving verification token from database..." -ForegroundColor $ColorYellow
Write-Host "  Email: $Email" -ForegroundColor Gray

$query = "SELECT token FROM email_verification_tokens WHERE email = '$Email' AND is_used = FALSE AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1;"

# Execute Docker command and capture output
$token = docker exec -i $DbContainer psql -U $DbUser -d $DbName -t -A -c $query 2>&1

# Handle ErrorRecord type from Docker
if ($token -is [System.Management.Automation.ErrorRecord]) {
    Write-Host "[ERROR] Database connection failed" -ForegroundColor $ColorRed
    Write-Host ""
    Write-Host "Error details:" -ForegroundColor $ColorYellow
    Write-Host "  $($token.Exception.Message)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor $ColorYellow
    Write-Host "  1. Check if Docker container is running:" -ForegroundColor Gray
    Write-Host "     docker ps --filter name=postgres" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Verify container name (current: $DbContainer)" -ForegroundColor Gray
    Write-Host "     docker ps" -ForegroundColor Gray
    exit 1
}

# Convert to string and clean
$token = $token | Out-String
$token = $token.Trim()

try {
    if ([string]::IsNullOrWhiteSpace($token) -or $token -match "error|ERROR") {
        Write-Host "[ERROR] No valid verification token found" -ForegroundColor $ColorRed
        Write-Host ""
        Write-Host "Possible reasons:" -ForegroundColor $ColorYellow
        Write-Host "  - User hasn't registered yet"
        Write-Host "  - Token has already been used"
        Write-Host "  - Token has expired (24 hour expiration)"
        Write-Host "  - Email address is incorrect"
        Write-Host "  - Database container name is wrong (current: $DbContainer)"
        Write-Host ""

        # Show token information if any exists
        Write-Host "Checking for any tokens for this email..." -ForegroundColor $ColorYellow
        $checkQuery = "SELECT token, created_at, expires_at, is_used FROM email_verification_tokens WHERE email = '$Email' ORDER BY created_at DESC LIMIT 3;"
        docker exec -i $DbContainer psql -U $DbUser -d $DbName -c $checkQuery

        exit 1
    }

    Write-Host "[SUCCESS] Token found" -ForegroundColor $ColorGreen
    $tokenPreview = $token.Substring(0, [Math]::Min(20, $token.Length)) + "..." + $token.Substring([Math]::Max(0, $token.Length - 10))
    Write-Host "  Token: $tokenPreview" -ForegroundColor Gray
    Write-Host ""

} catch {
    Write-Host "[ERROR] Failed to query database: $_" -ForegroundColor $ColorRed
    Write-Host ""
    Write-Host "Tip: Check if Docker container '$DbContainer' is running:" -ForegroundColor $ColorYellow
    Write-Host "  docker ps --filter name=postgres" -ForegroundColor Gray
    exit 1
}

# Step 2: Verify email using the API
Write-Host "[Step 2] Calling verification API..." -ForegroundColor $ColorYellow
Write-Host "  URL: $ApiUrl/api/v1/auth/verify-email" -ForegroundColor Gray

$body = @{
    token = $token
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$ApiUrl/api/v1/auth/verify-email" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -ErrorAction Stop

    Write-Host ""
    Write-Host "[SUCCESS] Email verified successfully!" -ForegroundColor $ColorGreen
    Write-Host ""
    Write-Host "Response:" -ForegroundColor $ColorGreen
    Write-Host "  $($response.message)" -ForegroundColor Gray
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "[ERROR] Verification failed" -ForegroundColor $ColorRed
    Write-Host "  Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor $ColorRed
    Write-Host "  Error: $($_.ErrorDetails.Message)" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# Step 3: Verify in database
Write-Host "[Step 3] Verifying database status..." -ForegroundColor $ColorYellow
$verifyQuery = "SELECT email, is_email_verified, email_verified_at FROM users WHERE email = '$Email';"
docker exec -i $DbContainer psql -U $DbUser -d $DbName -c $verifyQuery

Write-Host ""
Write-Host "================================================" -ForegroundColor $ColorGreen
Write-Host "     Verification Complete! [SUCCESS]" -ForegroundColor $ColorGreen
Write-Host "================================================" -ForegroundColor $ColorGreen
