"""
Core module tests.
Run with: pytest tests/test_core.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestSecurityFunctions:
    """Test security utility functions."""
    
    def test_generate_otp(self):
        """Test OTP generation."""
        from app.core.security import generate_otp
        
        otp = generate_otp()
        assert len(otp) == 6
        assert otp.isdigit()
        
        # Generate multiple to verify uniqueness
        otps = [generate_otp() for _ in range(10)]
        assert len(set(otps)) > 1  # Should be different
    
    def test_hash_otp(self):
        """Test OTP hashing."""
        from app.core.security import hash_otp
        
        otp = "123456"
        hashed = hash_otp(otp)
        
        assert hashed is not None
        assert hashed != otp
        assert len(hashed) > 0
    
    def test_verify_otp_correct(self):
        """Test OTP verification with correct code."""
        from app.core.security import hash_otp, verify_otp
        
        otp = "654321"
        hashed = hash_otp(otp)
        
        assert verify_otp(otp, hashed) is True
    
    def test_verify_otp_incorrect(self):
        """Test OTP verification with incorrect code."""
        from app.core.security import hash_otp, verify_otp
        
        otp = "654321"
        hashed = hash_otp(otp)
        
        assert verify_otp("000000", hashed) is False
    
    def test_password_hash_and_verify(self):
        """Test password hashing and verification."""
        from app.core.security import get_password_hash, verify_password
        
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False


class TestJWTFunctions:
    """Test JWT utility functions."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        from app.core.security import create_access_token
        
        # Token takes a dict with "sub" key
        token = create_access_token(data={"sub": "user-123", "role": "CUSTOMER"})
        
        assert token is not None
        assert len(token) > 0
        assert "." in token  # JWT format
    
    def test_decode_access_token(self):
        """Test access token decoding."""
        from app.core.security import create_access_token, decode_token
        
        token = create_access_token(data={"sub": "user-123", "role": "ADMIN"})
        
        # Decode using the app's decode function
        payload = decode_token(token)
        
        assert payload["sub"] == "user-123"
        assert payload["role"] == "ADMIN"
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token returns None."""
        from app.core.security import decode_token
        
        result = decode_token("invalid.token.here")
        assert result is None


class TestExceptions:
    """Test custom exception classes."""
    
    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        from app.core.exceptions import AuthenticationError
        from app.constants.error_codes import ErrorCode
        
        error = AuthenticationError(
            error_code=ErrorCode.INVALID_CREDENTIALS,
            message="Wrong password"
        )
        
        assert error.error_code == ErrorCode.INVALID_CREDENTIALS
    
    def test_permission_denied_error(self):
        """Test PermissionDeniedError exception (not AuthorizationError)."""
        from app.core.exceptions import PermissionDeniedError
        from app.constants.error_codes import ErrorCode
        
        error = PermissionDeniedError(
            error_code=ErrorCode.PERMISSION_DENIED,
            message="Access denied"
        )
        
        assert error.error_code == ErrorCode.PERMISSION_DENIED
    
    def test_not_found_error(self):
        """Test NotFoundError exception."""
        from app.core.exceptions import NotFoundError
        from app.constants.error_codes import ErrorCode
        
        error = NotFoundError(
            error_code=ErrorCode.USER_NOT_FOUND,
            message="User not found"
        )
        
        assert error.error_code == ErrorCode.USER_NOT_FOUND
    
    def test_conflict_error(self):
        """Test ConflictError exception."""
        from app.core.exceptions import ConflictError
        from app.constants.error_codes import ErrorCode
        
        error = ConflictError(
            error_code=ErrorCode.USER_ALREADY_EXISTS,
            message="User exists"
        )
        
        assert error.error_code == ErrorCode.USER_ALREADY_EXISTS
    
    def test_validation_error(self):
        """Test ValidationError exception."""
        from app.core.exceptions import ValidationError
        from app.constants.error_codes import ErrorCode
        
        error = ValidationError(
            error_code=ErrorCode.FIELD_INVALID,
            message="Invalid field",
            field="email"
        )
        
        assert error.error_code == ErrorCode.FIELD_INVALID
        assert error.field == "email"
    
    def test_rate_limit_error(self):
        """Test RateLimitError exception."""
        from app.core.exceptions import RateLimitError
        from app.constants.error_codes import ErrorCode
        
        error = RateLimitError(
            error_code=ErrorCode.OTP_COOLDOWN,
            message="Too many requests",
            retry_after=60
        )
        
        # Check the details contain retry_after
        assert error.details is not None
        assert error.details.get("retry_after") == 60


class TestConfig:
    """Test configuration settings."""
    
    def test_settings_instance(self):
        """Test settings can be instantiated."""
        from app.core.config import settings
        
        assert settings is not None
        assert hasattr(settings, 'SECRET_KEY')
        assert hasattr(settings, 'ALGORITHM')
        assert hasattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES')
    
    def test_settings_required_values(self):
        """Test that required settings have values."""
        from app.core.config import settings
        
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 0
        
        assert settings.ALGORITHM is not None
        
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0


class TestDocs:
    """Test documentation utilities."""
    
    def test_doc_responses(self):
        """Test doc_responses helper."""
        from app.core.docs import doc_responses
        
        responses = doc_responses(
            success_example={"id": "123"},
            success_message="Success",
            errors=(401, 403, 404)
        )
        
        assert isinstance(responses, dict)
        assert 401 in responses
        assert 403 in responses
        assert 404 in responses

