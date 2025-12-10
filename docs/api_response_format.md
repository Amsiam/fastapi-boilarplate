# API Response Format Documentation

## Overview
All API responses follow a standardized format to make frontend integration consistent and predictable.

## Success Response Format

All successful API responses follow this structure:

```json
{
  "success": true,
  "message": "Human-readable success message",
  "data": {
    // Response payload (can be object, array, or null)
  }
}
```

### Fields:
- **`success`** (boolean): Always `true` for successful responses
- **`message`** (string): Human-readable message describing the operation
- **`data`** (any): The actual response payload. Can be:
  - Object: `{"id": "123", "name": "John"}`
  - Array: `[{"id": "1"}, {"id": "2"}]`
  - Null: `null` (for operations with no return data)

### Examples:

**User Registration Success:**
```json
{
  "success": true,
  "message": "User registered successfully. Please verify your email.",
  "data": null
}
```

**Login Success:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

**Get User Profile:**
```json
{
  "success": true,
  "message": "User profile retrieved",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_verified": true
  }
}
```

---

## Error Response Format

All error responses follow this structure:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "field": "fieldName"  // Optional, only for field-specific errors
  },
  "details": {
    // Optional additional context
  }
}
```

### Fields:
- **`success`** (boolean): Always `false` for errors
- **`error`** (object): Error information
  - **`code`** (string): Machine-readable error code (e.g., `AUTH_001`)
  - **`message`** (string): Human-readable error message
  - **`field`** (string|null): Field name if error is field-specific
- **`details`** (object|null): Optional additional error context

### Error Codes Reference:

#### Authentication Errors (AUTH_xxx)
- `AUTH_001`: Invalid credentials
- `AUTH_002`: Email not verified
- `AUTH_003`: Account inactive
- `AUTH_004`: Invalid token
- `AUTH_005`: Token expired
- `AUTH_006`: Invalid refresh token

#### OTP Errors (OTP_xxx)
- `OTP_001`: Invalid OTP
- `OTP_002`: OTP expired
- `OTP_003`: Maximum attempts exceeded
- `OTP_004`: Cooldown period active
- `OTP_005`: Account locked due to too many attempts

#### User Errors (USER_xxx)
- `USER_001`: User not found
- `USER_002`: User already exists
- `USER_003`: User inactive

#### Permission Errors (PERM_xxx)
- `PERM_001`: Permission denied
- `PERM_002`: Insufficient permissions
- `PERM_003`: Admin access required

#### Validation Errors (VAL_xxx)
- `VAL_001`: General validation error
- `VAL_002`: Required field missing
- `VAL_003`: Invalid field value

#### Rate Limit Errors (RATE_xxx)
- `RATE_001`: Rate limit exceeded
- `RATE_002`: Too many requests

### Error Examples:

**Invalid Credentials (401):**
```json
{
  "success": false,
  "error": {
    "code": "AUTH_001",
    "message": "Invalid email or password",
    "field": null
  },
  "details": null
}
```

**Email Already Exists (409):**
```json
{
  "success": false,
  "error": {
    "code": "USER_002",
    "message": "User with this email already exists",
    "field": "email"
  },
  "details": null
}
```

**Validation Error (422):**
```json
{
  "success": false,
  "error": {
    "code": "VAL_001",
    "message": "Request validation failed",
    "field": null
  },
  "errors": [
    {
      "code": "VAL_002",
      "message": "Email is required",
      "field": "email"
    },
    {
      "code": "VAL_003",
      "message": "Password must be at least 8 characters",
      "field": "password"
    }
  ]
}
```

**Rate Limit Exceeded (429):**
```json
{
  "success": false,
  "error": {
    "code": "RATE_001",
    "message": "Too many requests. Please try again later.",
    "field": null
  },
  "details": {
    "retry_after": 60
  }
}
```

---

## Frontend Integration Guide

### Checking Response Status

```typescript
// TypeScript example
interface SuccessResponse<T = any> {
  success: true;
  message: string;
  data: T;
}

interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    field?: string;
  };
  details?: any;
}

type ApiResponse<T = any> = SuccessResponse<T> | ErrorResponse;

// Usage
async function handleApiCall<T>(promise: Promise<Response>): Promise<T> {
  const response = await promise;
  const data: ApiResponse<T> = await response.json();
  
  if (data.success) {
    return data.data;
  } else {
    throw new Error(data.error.message);
  }
}
```

### Error Handling by Code

```typescript
function handleError(error: ErrorResponse) {
  switch (error.error.code) {
    case 'AUTH_001':
      // Show "Invalid credentials" message
      showLoginError(error.error.message);
      break;
    
    case 'AUTH_002':
      // Redirect to email verification page
      redirectToVerification();
      break;
    
    case 'RATE_001':
      // Show rate limit message with retry time
      const retryAfter = error.details?.retry_after || 60;
      showRateLimitMessage(retryAfter);
      break;
    
    case 'VAL_001':
      // Handle validation errors (check for errors array)
      if ('errors' in error) {
        showValidationErrors(error.errors);
      }
      break;
    
    default:
      // Generic error handling
      showGenericError(error.error.message);
  }
}
```

---

## HTTP Status Codes

- **200 OK**: Successful GET, PUT, PATCH requests
- **201 Created**: Successful POST request (resource created)
- **204 No Content**: Successful DELETE request
- **400 Bad Request**: Invalid request
- **401 Unauthorized**: Authentication required or failed
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource already exists
- **422 Unprocessable Entity**: Validation error
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

---

## Best Practices

1. **Always check `success` field first**
   ```typescript
   if (response.success) {
     // Handle success
   } else {
     // Handle error
   }
   ```

2. **Use error codes for logic, messages for display**
   - Error codes are stable and won't change
   - Messages are human-readable and may be updated

3. **Handle validation errors specially**
   - Check for `errors` array in validation responses
   - Map errors to form fields using the `field` property

4. **Respect rate limits**
   - Use `retry_after` from details to implement backoff
   - Show user-friendly countdown timers

5. **Store tokens securely**
   - Access tokens: Memory only (never localStorage)
   - Refresh tokens: HttpOnly cookies (handled by browser)
