"""
Constants and Enums tests.
"""
from app.constants.enums import UserType, OTPType
from app.constants.error_codes import ErrorCode

class TestEnums:
    """Test enum values."""
    
    def test_user_roles(self):
        """Test UserType enum values exist."""
        assert UserType.CUSTOMER is not None
        assert UserType.ADMIN is not None
    
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
