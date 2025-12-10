# API Error Codes

This document outlines the standardized error codes returned by the API. Each error response includes an `error_code` field to help clients handle specific error scenarios programmatically.

## Error Response Format

Errors are returned in a standardized JSON structure. There are two main types:

### Standard Error
Used for logic errors, authentication failures, etc.

```json
{
  "success": false,
  "error": {
    "code": "AUTH_001",
    "message": "Invalid credentials",
    "field": null
  },
  "details": null
}
```

### Validation Error
Used when request data fails validation (HTTP 422). Includes a list of specific field errors.

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "field": null
  },
  "errors": [
    {
      "code": "FIELD_REQUIRED",
      "message": "Email is required",
      "field": "email"
    },
    {
      "code": "FIELD_INVALID",
      "message": "Password too short",
      "field": "password"
    }
  ]
}
```

## Authentication Errors
| Error Code | Constant | Description |
|:-----------|:---------|:------------|
| `AUTH_001` | `INVALID_CREDENTIALS` | The email or password provided is incorrect. |
| `AUTH_002` | `EMAIL_NOT_VERIFIED` | Account exists but the email address has not been verified. |
| `AUTH_003` | `ACCOUNT_LOCKED` | The account has been locked due to too many failed login attempts or admin action. |
| `AUTH_004` | `INVALID_TOKEN` | The provided authentication token is invalid or malformed. |
| `AUTH_005` | `TOKEN_EXPIRED` | The authentication token has expired. Please refresh or login again. |
| `AUTH_006` | `INVALID_REFRESH_TOKEN` | The refresh token is invalid, expired, or revoked. |
| `AUTH_007` | `ACCOUNT_INACTIVE` | The account has been deactivated. |

## OAuth Errors
| Error Code | Constant | Description |
|:-----------|:---------|:------------|
| `OAUTH_001` | `OAUTH_ERROR` | General OAuth provider error or communication failure. |
| `OAUTH_002` | `OAUTH_STATE_INVALID` | OAuth state parameter validation failed (CSRF protection). |
| `OAUTH_003` | `OAUTH_PROVIDER_NOT_FOUND` | The specified OAuth provider is not supported or not configured. |
| `OAUTH_004` | `OAUTH_ACCOUNT_ALREADY_LINKED` | This OAuth account is already linked to another user. |
| `OAUTH_005` | `OAUTH_PROVIDER_HAS_ACCOUNTS` | Cannot delete an OAuth provider that has active user accounts linked. |
| `OAUTH_006` | `DUPLICATE_ENTRY` | The OAuth provider configuration already exists. |

## User Management Errors
| Error Code | Constant | Description |
|:-----------|:---------|:------------|
| `USER_001` | `USER_NOT_FOUND` | The requested user could not be found. |
| `USER_002` | `USER_ALREADY_EXISTS` | A user with this email address already exists. |

## OTP (One-Time Password) Errors
| Error Code | Constant | Description |
|:-----------|:---------|:------------|
| `OTP_001` | `OTP_INVALID` | The provided OTP code is incorrect. |
| `OTP_002` | `OTP_EXPIRED` | The OTP code has expired. |
| `OTP_003` | `OTP_MAX_ATTEMPTS` | Maximum allowed attempts for this OTP have been reached. |
| `OTP_004` | `OTP_COOLDOWN` | A new OTP cannot be generated yet (cooldown period active). |
| `OTP_005` | `OTP_LOCKED` | OTP verification is temporarily locked due to excessive failures. |

## Permission Errors
| Error Code | Constant | Description |
|:-----------|:---------|:------------|
| `PERM_001` | `PERMISSION_DENIED` | The user doesn't have the necessary permissions for this action. |
| `PERM_002` | `ROLE_NOT_FOUND` | The specified role does not exist. |
| `PERM_003` | `PERMISSION_NOT_FOUND` | The specified permission does not exist. |
| `PERM_004` | `PERMISSION_ALREADY_EXISTS` | The permission code already exists. |

## Role Errors
| Error Code | Constant | Description |
|:-----------|:---------|:------------|
| `ROLE_001` | `ROLE_ALREADY_EXISTS` | A role with this name already exists. |
| `ROLE_002` | `CANNOT_MODIFY_SYSTEM_ROLE` | System roles (e.g. SUPER_ADMIN) cannot be modified or deleted. |
| `ROLE_003` | `CANNOT_DELETE_ROLE_IN_USE` | The role cannot be deleted because it is assigned to users. |

## Validation Errors
| Error Code | Constant | Description |
|:-----------|:---------|:------------|
| `VAL_001` | `VALIDATION_ERROR` | The request data failed validation rules. |
| `VAL_002` | `FIELD_REQUIRED` | A required field is missing from the request. |
| `VAL_003` | `FIELD_INVALID` | A field contains invalid data (wrong format, type, etc.). |

## Rate Limiting Errors
| Error Code | Constant | Description |
|:-----------|:---------|:------------|
| `RATE_001` | `RATE_LIMIT_EXCEEDED` | Too many requests. Please try again later. |

## Server Errors
| Error Code | Constant | Description |
|:-----------|:---------|:------------|
| `SRV_001` | `INTERNAL_ERROR` | An unexpected internal server error occurred. |
| `SRV_002` | `DATABASE_ERROR` | A database operation failed. |
| `SRV_003` | `EXTERNAL_SERVICE_ERROR` | A call to an external service (e.g. Email, AWS) failed. |
