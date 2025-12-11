"""
Auth Schema tests.
"""
import pytest
from pydantic import ValidationError
from app.modules.auth.schemas import (
    UserRegisterRequest,
    LoginRequest,
    EmailVerificationRequest,
    ResendOTPRequest
)

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
