"""
Error code constants for standardized error responses.
"""


class ErrorCode:
    """Standardized error codes for API responses."""
    
    # Authentication errors (AUTH_xxx)
    INVALID_CREDENTIALS = "AUTH_001"
    EMAIL_NOT_VERIFIED = "AUTH_002"
    ACCOUNT_LOCKED = "AUTH_003"
    INVALID_TOKEN = "AUTH_004"
    TOKEN_EXPIRED = "AUTH_005"
    INVALID_REFRESH_TOKEN = "AUTH_006"
    ACCOUNT_INACTIVE = "AUTH_007"
    
    # User errors (USER_xxx)
    USER_NOT_FOUND = "USER_001"
    USER_ALREADY_EXISTS = "USER_002"
    
    # OTP errors (OTP_xxx)
    OTP_INVALID = "OTP_001"
    OTP_EXPIRED = "OTP_002"
    OTP_MAX_ATTEMPTS = "OTP_003"
    OTP_COOLDOWN = "OTP_004"
    OTP_LOCKED = "OTP_005"
    
    # Permission errors (PERM_xxx)
    PERMISSION_DENIED = "PERM_001"
    ROLE_NOT_FOUND = "PERM_002"
    PERMISSION_NOT_FOUND = "PERM_003"
    PERMISSION_ALREADY_EXISTS = "PERM_004"
    
    # Role errors (ROLE_xxx)
    ROLE_ALREADY_EXISTS = "ROLE_001"
    CANNOT_MODIFY_SYSTEM_ROLE = "ROLE_002"
    CANNOT_DELETE_ROLE_IN_USE = "ROLE_003"
    
    # Validation errors (VAL_xxx)
    VALIDATION_ERROR = "VAL_001"
    FIELD_REQUIRED = "VAL_002"
    FIELD_INVALID = "VAL_003"
    
    # Rate limiting (RATE_xxx)
    RATE_LIMIT_EXCEEDED = "RATE_001"
    
    # Server errors (SRV_xxx)
    INTERNAL_ERROR = "SRV_001"
    DATABASE_ERROR = "SRV_002"
    EXTERNAL_SERVICE_ERROR = "SRV_003"
