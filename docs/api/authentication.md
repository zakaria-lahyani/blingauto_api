# Authentication

## Overview

The API uses JWT (JSON Web Tokens) for authentication with access and refresh token patterns.

## Token Types

### Access Token
- **Purpose**: API access authorization
- **Expiry**: 1 hour
- **Location**: Authorization header: `Bearer {access_token}`

### Refresh Token
- **Purpose**: Renew access tokens
- **Expiry**: 30 days
- **Storage**: Secure HTTP-only cookie (recommended) or client storage

## Authentication Flow

1. **Register/Login** → Receive access + refresh tokens
2. **API Requests** → Include access token in Authorization header
3. **Token Expiry** → Use refresh token to get new access token
4. **Logout** → Invalidate refresh token

## Endpoints

### POST /api/v1/auth/register
Register a new user account.

### POST /api/v1/auth/login
Authenticate user and receive tokens.

### POST /api/v1/auth/refresh
Refresh access token using refresh token.

### POST /api/v1/auth/logout
Invalidate refresh token and log out.

## Authorization

### User Roles
- **client**: Regular customer (default)
- **washer**: Service provider
- **admin**: System administrator

### Permission Levels
- **Public**: No authentication required
- **Authenticated**: Valid access token required
- **Role-based**: Specific role required
- **Owner**: Resource owner or admin access

## Security Headers

All API responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`