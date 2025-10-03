@echo off
REM BlingAuto Email Verification Helper Script (Windows)
REM This script helps verify user emails by getting the token from the database
REM and calling the verification API endpoint

setlocal enabledelayedexpansion

REM Configuration
if "%API_URL%"=="" set API_URL=http://localhost:8000
if "%DB_CONTAINER%"=="" set DB_CONTAINER=blingauto_api-db-1

REM Check if email parameter is provided
if "%~1"=="" (
    echo Error: Email address required
    echo.
    echo Usage:
    echo   %~nx0 ^<email^>
    echo.
    echo Example:
    echo   %~nx0 verifytest123456@example.com
    echo.
    echo Environment Variables:
    echo   API_URL      - API base URL ^(default: http://localhost:8000^)
    echo   DB_CONTAINER - Database container name ^(default: blingauto_api-db-1^)
    echo.
    exit /b 1
)

set EMAIL=%~1

echo ================================================
echo    BlingAuto Email Verification Helper
echo ================================================
echo.

REM Step 1: Get verification token from database
echo [Step 1] Retrieving verification token from database...
echo   Email: %EMAIL%

for /f "delims=" %%i in ('docker exec -i %DB_CONTAINER% psql -U postgres -d blingauto -t -A -c "SELECT token FROM email_verification_tokens WHERE email = '%EMAIL%' AND is_used = FALSE AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1;"') do set TOKEN=%%i

REM Remove any trailing whitespace
set TOKEN=%TOKEN: =%

if "%TOKEN%"=="" (
    echo [ERROR] No valid verification token found
    echo.
    echo Possible reasons:
    echo   - User hasn't registered yet
    echo   - Token has already been used
    echo   - Token has expired ^(24 hour expiration^)
    echo   - Email address is incorrect
    echo.
    echo Checking for any tokens for this email...
    docker exec -i %DB_CONTAINER% psql -U postgres -d blingauto -c "SELECT token, created_at, expires_at, is_used FROM email_verification_tokens WHERE email = '%EMAIL%' ORDER BY created_at DESC LIMIT 3;"
    exit /b 1
)

echo [SUCCESS] Token found
echo   Token: %TOKEN:~0,20%...%TOKEN:~-10%
echo.

REM Step 2: Verify email using the API
echo [Step 2] Calling verification API...
echo   URL: %API_URL%/api/v1/auth/verify-email

REM Create temporary JSON file
echo {"token": "%TOKEN%"} > %TEMP%\verify_token.json

REM Call API
curl -s -X POST "%API_URL%/api/v1/auth/verify-email" ^
    -H "Content-Type: application/json" ^
    -d @%TEMP%\verify_token.json > %TEMP%\verify_response.json

REM Delete temp JSON file
del %TEMP%\verify_token.json

echo.

REM Check if verification was successful (look for success message)
findstr /C:"verified successfully" %TEMP%\verify_response.json >nul
if %ERRORLEVEL%==0 (
    echo [SUCCESS] Email verified successfully!
    echo.
    echo Response:
    type %TEMP%\verify_response.json
    echo.

    REM Verify in database
    echo [Step 3] Verifying database status...
    docker exec -i %DB_CONTAINER% psql -U postgres -d blingauto -c "SELECT email, is_email_verified, email_verified_at FROM users WHERE email = '%EMAIL%';"

    echo.
    echo ================================================
    echo        Verification Complete!
    echo ================================================
) else (
    echo [ERROR] Verification failed
    echo.
    echo Response:
    type %TEMP%\verify_response.json
    echo.
    del %TEMP%\verify_response.json
    exit /b 1
)

del %TEMP%\verify_response.json
endlocal
