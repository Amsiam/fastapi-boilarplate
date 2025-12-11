"""
Enums for the application.
"""
from enum import Enum


class UserType(str, Enum):
    """User type discriminator."""
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"


class OTPType(str, Enum):
    """OTP types for verification."""
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    PASSWORD_RESET = "PASSWORD_RESET"
