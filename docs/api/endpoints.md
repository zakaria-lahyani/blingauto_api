# API Endpoints Reference

Complete API reference with examples - see main README for full documentation.

**Base URL**: `/api/v1`

## Authentication Endpoints
- POST `/auth/register` - Register new user
- POST `/auth/login` - Login
- POST `/auth/refresh` - Refresh token
- GET `/auth/me` - Get current user
- POST `/auth/logout` - Logout
- More endpoints documented in [API README](./README.md)

## Booking Endpoints
- POST `/bookings` - Create booking
- GET `/bookings` - List bookings
- GET `/bookings/{id}` - Get booking
- POST `/bookings/{id}/confirm` - Confirm
- POST `/bookings/{id}/start` - Start service
- POST `/bookings/{id}/complete` - Complete
- POST `/bookings/{id}/cancel` - Cancel
- More endpoints documented in [API README](./README.md)

See [API README](./README.md) for complete documentation.
