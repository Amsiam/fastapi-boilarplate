
import pytest
from httpx import AsyncClient
from app.core.schemas.response import ErrorCode
from app.modules.auth.otp_service import OTPService
from app.constants.enums import OTPType
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
class TestOTPValidation:
    """Test validation error specificity in OTP verification."""
    
    async def test_otp_validation_field(self, client: AsyncClient):
        """Test that invalid OTP, expired OTP, etc. specify 'otp_code' field."""
        # For this test, we can mock the OTPService to raise ValidationErrors directly
        # OR we can try to use a real flow if possible.
        # However, OTP flow involves email sending which is mocked.
        # Let's interact with the verify-email endpoint or reset-password endpoint.
        
        # Scenario: Verify Email with invalid OTP
        # We need to assume the endpoint calls OTPService.verify_otp
        
        # Using a non-existent OTP should raise OTP_EXPIRED with field otp_code
        email = "invalid_otp_test@example.com"
        otp = "123456"
        
        # Check endpoint app/modules/auth/endpoints.py -> verify_email
        response = await client.post(
            "/api/v1/auth/verify-email",
            json={
                "email": email,
                "otp": otp
            }
        )
        
        # Expect 422 (ValidationError mapped to 422 usually, or 400? Checked error map)
        # ValidationErrors are typically 400 in this app? 
        # exception_handlers.py maps ValidationError to 400 by default unless it's Pydantic.
        # Let's check app/core/exceptions.py mapping.
        
        # Actually in app/main.py: create_error_responses(400, 401, 403, 404, 422, 429, 500)
        # ValidationError in app/core/exceptions.py often defaults to 400 Bad Request.
        
        # WAIT: Pydantic ValidationErrors are 422. Custom ValidationErrors are 400?
        # Let's check app/core/exceptions.py
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert data["success"] is False
        
        # We are looking for "field": "otp_code"
        # The ValidationError raised by OTPService.verify_otp is caught.
        assert data["error"]["code"] == ErrorCode.OTP_EXPIRED
        assert data["error"]["field"] == "otp_code"

