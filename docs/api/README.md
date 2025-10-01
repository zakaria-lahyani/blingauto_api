# API Reference

Complete API documentation for BlingAuto Car Wash API.

**Base URL**: Production: `https://api.blingauto.com/api/v1` | Development: `http://localhost:8000/api/v1`

**Current Version**: v1.0.0

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Patterns](#common-patterns)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Endpoints by Feature](#endpoints-by-feature)
   - [Authentication](#authentication-endpoints)
   - [Bookings](#bookings-endpoints)
   - [Services & Categories](#services--categories-endpoints)
   - [Vehicles](#vehicles-endpoints)
   - [Scheduling](#scheduling-endpoints)

---

## Overview

### API Characteristics

- **RESTful**: Standard REST principles with resource-based URLs
- **JSON**: All requests and responses use JSON
- **Versioned**: `/api/v1/` prefix for all endpoints
- **Authenticated**: JWT-based authentication
- **Rate Limited**: 100 requests/minute for general API, 10 requests/minute for auth endpoints

### Quick Start

```bash
# 1. Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!","full_name":"John Doe"}'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'

# 3. Use access token
curl -X GET http://localhost:8000/api/v1/bookings \
  -H "Authorization: Bearer <access_token>"
```

---

## Authentication

All API requests (except registration, login, and public endpoints) require authentication using JWT Bearer tokens.

### Obtaining Tokens

**POST** `/auth/login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Using Tokens

Include the access token in the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

### Token Lifecycle

- **Access Token**: 15 minutes
- **Refresh Token**: 7 days

---

## Common Patterns

### Pagination

List endpoints support pagination via query parameters:

```http
GET /api/v1/bookings?page=1&limit=20
```

**Parameters:**
- `page` (integer): Page number, default 1
- `limit` (integer): Items per page, default 20, max 100

**Response:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

### Date/Time Format

All dates use **ISO 8601** format with UTC timezone:

```json
{
  "scheduled_at": "2025-10-02T14:30:00Z",
  "created_at": "2025-10-01T10:15:30.123Z"
}
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Human-readable error message",
  "code": "ERROR_CODE",
  "field": "field_name",
  "timestamp": "2025-10-01T10:15:30Z"
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PATCH, DELETE |
| 201 | Created | Successful POST |
| 400 | Bad Request | Validation error |
| 401 | Unauthorized | Missing/invalid auth |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

See [error-handling.md](./error-handling.md) for details.

---

## Rate Limiting

- **General API**: 100 requests/minute
- **Auth Endpoints**: 10 requests/minute
- **Per IP address**

**Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1633024800
```

---

## Endpoints by Feature

### Authentication Endpoints

See [authentication.md](./authentication.md) for complete authentication documentation.

**Key Endpoints:**
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login
- `POST /auth/refresh` - Refresh token
- `GET /auth/me` - Get current user
- `PATCH /auth/me` - Update profile
- `POST /auth/password/change` - Change password
- `POST /auth/password/reset/request` - Request password reset
- `POST /auth/password/reset/confirm` - Reset password
- `POST /auth/email/verify` - Verify email

### Bookings Endpoints

**Create Booking**

`POST /bookings`

**Roles**: CLIENT, MANAGER, ADMIN

**Request:**
```json
{
  "customer_id": "user-uuid",
  "vehicle_id": "vehicle-uuid",
  "service_ids": ["service-1", "service-2"],
  "scheduled_at": "2025-10-02T14:30:00Z",
  "notes": "Please focus on exterior",
  "booking_type": "SCHEDULED"
}
```

**Response (201):**
```json
{
  "id": "booking-uuid",
  "status": "PENDING",
  "total_price": "89.99",
  "estimated_duration_minutes": 60,
  "created_at": "2025-10-01T10:15:30Z"
}
```

**Other Booking Endpoints:**
- `GET /bookings` - List bookings (paginated)
- `GET /bookings/{id}` - Get booking details
- `POST /bookings/{id}/confirm` - Confirm booking (MANAGER)
- `POST /bookings/{id}/start` - Start service (WASHER)
- `POST /bookings/{id}/complete` - Complete service (WASHER)
- `POST /bookings/{id}/cancel` - Cancel booking
- `POST /bookings/{id}/no-show` - Mark as no-show (MANAGER)

### Services & Categories Endpoints

- `GET /categories` - List all categories
- `GET /services` - List services (filterable by category)
- `GET /services/{id}` - Get service details
- `POST /services` - Create service (ADMIN)
- `PATCH /services/{id}` - Update service (ADMIN)
- `DELETE /services/{id}` - Delete service (ADMIN)

### Vehicles Endpoints

- `GET /vehicles` - List user's vehicles
- `POST /vehicles` - Add vehicle
- `GET /vehicles/{id}` - Get vehicle details
- `PATCH /vehicles/{id}` - Update vehicle
- `DELETE /vehicles/{id}` - Delete vehicle (soft delete)

### Scheduling Endpoints

- `GET /scheduling/availability` - Check time slot availability
- `POST /scheduling/suggestions` - Get AI-suggested times
- `GET /scheduling/capacity` - Get daily capacity info

---

## RBAC (Role-Based Access Control)

### Roles

- **CLIENT**: Regular customers
- **WASHER**: Service providers
- **MANAGER**: Facility managers
- **ADMIN**: System administrators

### Permission Matrix

| Action | CLIENT | WASHER | MANAGER | ADMIN |
|--------|--------|--------|---------|-------|
| Create booking | Own | No | Yes | Yes |
| View bookings | Own | Assigned | All | All |
| Confirm booking | No | No | Yes | Yes |
| Start/Complete | No | Assigned | Yes | Yes |
| Cancel booking | Own (before confirm) | No | Yes | Yes |
| Manage services | No | No | No | Yes |
| Manage users | No | No | No | Yes |

---

## Interactive Documentation

Visit the interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs` (development) or `https://api.blingauto.com/docs` (production)
- **ReDoc**: `http://localhost:8000/redoc` (development) or `https://api.blingauto.com/redoc` (production)

---

## Additional Resources

- [Authentication Guide](./authentication.md) - Detailed authentication flow
- [Error Handling](./error-handling.md) - Error codes and handling
- [Endpoints Directory](./endpoints/) - Detailed endpoint documentation
- [Schemas Directory](./schemas/) - Request/response schemas
- [Architecture Documentation](../architecture/README.md)
- [Features Documentation](../features/README.md)

---

## Changelog

### v1.0.0 (2025-10-01)

- Initial API release
- Authentication and authorization with JWT
- RBAC with 4 roles
- Bookings management with state machine
- Services and categories CRUD
- Vehicles management
- Scheduling system with availability checking

---

**Last Updated**: 2025-10-01