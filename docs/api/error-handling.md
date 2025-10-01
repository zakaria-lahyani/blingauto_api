# Error Handling

## Standard Error Format

All API errors follow a consistent JSON format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional error context (optional)",
    "field": "field_name (for validation errors)"
  }
}
```

## HTTP Status Codes

### 400 Bad Request
- Invalid request format
- Validation errors
- Business rule violations

### 401 Unauthorized
- Missing authentication token
- Invalid or expired token
- Insufficient permissions

### 403 Forbidden
- Valid token but insufficient role/permissions
- Resource access denied

### 404 Not Found
- Resource does not exist
- Endpoint not found

### 409 Conflict
- Resource already exists
- Concurrent modification conflict

### 422 Unprocessable Entity
- Validation errors
- Business rule violations

### 429 Too Many Requests
- Rate limit exceeded
- Try again after specified time

### 500 Internal Server Error
- Unexpected server error
- Database connection issues

## Error Codes

### Authentication Errors
- `AUTH_REQUIRED`: Authentication required
- `AUTH_INVALID`: Invalid credentials
- `AUTH_EXPIRED`: Token expired
- `AUTH_INSUFFICIENT`: Insufficient permissions

### Validation Errors
- `VALIDATION_FAILED`: Input validation failed
- `FIELD_REQUIRED`: Required field missing
- `FIELD_INVALID`: Field format invalid
- `FIELD_TOO_LONG`: Field exceeds maximum length

### Business Rule Errors
- `BUSINESS_RULE_VIOLATION`: Business rule violated
- `RESOURCE_CONFLICT`: Resource state conflict
- `OPERATION_NOT_ALLOWED`: Operation not permitted

### Resource Errors
- `RESOURCE_NOT_FOUND`: Resource not found
- `RESOURCE_ALREADY_EXISTS`: Resource already exists
- `RESOURCE_DELETED`: Resource has been deleted

## Rate Limiting

When rate limits are exceeded:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "retry_after": 60
  }
}
```

Headers included:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Window reset time (Unix timestamp)