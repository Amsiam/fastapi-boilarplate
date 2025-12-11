"""
Model and schema tests.
Run with: pytest tests/test_models.py -v
"""
import pytest
from uuid import uuid4
from datetime import datetime
from pydantic import ValidationError

from app.modules.auth.schemas import (
    UserRegisterRequest,
    LoginRequest,
    EmailVerificationRequest,
    ResendOTPRequest,
    ResetPasswordRequest
)
from app.modules.roles.schemas import (
    RoleCreateRequest,
    RoleUpdateRequest,
    PermissionCreateRequest
)
from app.constants.enums import UserRole, OTPType
from app.constants.error_codes import ErrorCode


class TestUserRegisterRequest:
    """Test UserRegisterRequest schema validation."""
    
    def test_valid_registration(self):
        """Test valid registration data."""
        data = UserRegisterRequest(
            email="test@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Doe"
        )
        assert data.email == "test@example.com"
    
    def test_invalid_email(self):
        """Test registration with invalid email."""
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                email="not-an-email",
                password="SecurePass123!",
                first_name="John",
                last_name="Doe"
            )
    
    def test_short_password(self):
        """Test registration with short password."""
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                email="test@example.com",
                password="short",
                first_name="John",
                last_name="Doe"
            )
    
    def test_empty_first_name(self):
        """Test registration with empty first name."""
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                email="test@example.com",
                password="SecurePass123!",
                first_name="",
                last_name="Doe"
            )
    
    def test_optional_phone_number(self):
        """Test registration with optional phone number."""
        data = UserRegisterRequest(
            email="test@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Doe",
            phone_number="+1234567890"
        )
        assert data.phone_number == "+1234567890"


class TestLoginRequest:
    """Test LoginRequest schema validation."""
    
    def test_valid_login(self):
        """Test valid login data."""
        data = LoginRequest(
            username="test@example.com",
            password="password123"
        )
        assert data.username == "test@example.com"
    
    def test_invalid_username_email(self):
        """Test login with invalid email format."""
        with pytest.raises(ValidationError):
            LoginRequest(
                username="not-an-email",
                password="password123"
            )


class TestEmailVerificationRequest:
    """Test EmailVerificationRequest schema validation."""
    
    def test_valid_verification(self):
        """Test valid verification data."""
        data = EmailVerificationRequest(
            email="test@example.com",
            otp="123456"
        )
        assert data.otp == "123456"
    
    def test_short_otp(self):
        """Test verification with short OTP."""
        with pytest.raises(ValidationError):
            EmailVerificationRequest(
                email="test@example.com",
                otp="12345"
            )
    
    def test_long_otp(self):
        """Test verification with long OTP."""
        with pytest.raises(ValidationError):
            EmailVerificationRequest(
                email="test@example.com",
                otp="1234567"
            )


class TestResendOTPRequest:
    """Test ResendOTPRequest schema validation."""
    
    def test_valid_email_verification_type(self):
        """Test valid resend OTP for email verification."""
        data = ResendOTPRequest(
            email="test@example.com",
            type="EMAIL_VERIFICATION"
        )
        assert data.type == "EMAIL_VERIFICATION"
    
    def test_valid_password_reset_type(self):
        """Test valid resend OTP for password reset."""
        data = ResendOTPRequest(
            email="test@example.com",
            type="PASSWORD_RESET"
        )
        assert data.type == "PASSWORD_RESET"
    
    def test_invalid_type(self):
        """Test resend OTP with invalid type."""
        with pytest.raises(ValidationError):
            ResendOTPRequest(
                email="test@example.com",
                type="INVALID_TYPE"
            )


class TestRoleSchemas:
    """Test role-related schemas."""
    
    def test_role_create_request(self):
        """Test valid role creation."""
        data = RoleCreateRequest(
            name="CUSTOM_ROLE",
            description="A custom role"
        )
        assert data.name == "CUSTOM_ROLE"
    
    def test_role_update_request(self):
        """Test valid role update (no name field in update)."""
        data = RoleUpdateRequest(
            description="Updated description"
        )
        assert data.description == "Updated description"
    
    def test_permission_create_request(self):
        """Test valid permission creation."""
        data = PermissionCreateRequest(
            code="custom:action",
            description="Custom permission",
            resource="custom",
            action="action"
        )
        assert data.code == "custom:action"
        assert data.resource == "custom"


class TestEnums:
    """Test enum values."""
    
    def test_user_roles(self):
        """Test UserRole enum values exist."""
        assert UserRole.CUSTOMER is not None
        assert UserRole.ADMIN is not None
    
    def test_otp_types(self):
        """Test OTPType enum values exist."""
        assert OTPType.EMAIL_VERIFICATION is not None
        assert OTPType.PASSWORD_RESET is not None


class TestErrorCodes:
    """Test error code constants."""
    
    def test_auth_error_codes(self):
        """Test authentication error codes exist."""
        assert ErrorCode.INVALID_CREDENTIALS == "AUTH_001"
        assert ErrorCode.EMAIL_NOT_VERIFIED == "AUTH_002"
        assert ErrorCode.INVALID_TOKEN == "AUTH_004"
    
    def test_oauth_error_codes(self):
        """Test OAuth error codes exist."""
        assert ErrorCode.OAUTH_ERROR == "OAUTH_001"
        assert ErrorCode.OAUTH_PROVIDER_NOT_FOUND == "OAUTH_003"
    
    def test_otp_error_codes(self):
        """Test OTP error codes exist."""
        assert ErrorCode.OTP_INVALID == "OTP_001"
        assert ErrorCode.OTP_EXPIRED == "OTP_002"
        assert ErrorCode.OTP_COOLDOWN == "OTP_004"
    
    def test_permission_error_codes(self):
        """Test permission error codes exist."""
        assert ErrorCode.PERMISSION_DENIED == "PERM_001"
        assert ErrorCode.ROLE_NOT_FOUND == "PERM_002"
