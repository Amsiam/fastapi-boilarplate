"""
Enums for the application.
"""
from enum import Enum


class UserRole(str, Enum):
    """User role types."""
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"


class OTPType(str, Enum):
    """OTP types for verification."""
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    PASSWORD_RESET = "PASSWORD_RESET"
