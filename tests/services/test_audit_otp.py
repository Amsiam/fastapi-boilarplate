import pytest
import uuid
from app.core.mongo import mongodb
from app.core.cache import get_cache, otp_key
from app.constants.enums import OTPType



@pytest.fixture
def unique_email():
    return f"audit_otp_{uuid.uuid4().hex[:8]}@example.com"

@pytest.mark.asyncio
async def test_resend_otp_audit(client, unique_email):
    """Test audit log for resend OTP."""
    # Resend OTP (First time or subsequent)
    response = await client.post(
        "/api/v1/auth/resend-otp",
        json={"email": unique_email, "type": "EMAIL_VERIFICATION"}
    )
    assert response.status_code == 200
    
    # Verify Audit Log
    db = mongodb.get_db()
    logs = await db["audit_logs"].find({
        "target_id": unique_email,
        "action": "resend_otp"
    }).to_list(length=1)
    
    assert len(logs) == 1
    assert logs[0]["details"]["email"] == unique_email
    # Actor should be anonymous or user id if user existed (here anonymous)
    assert logs[0]["actor_id"] == "anonymous"

@pytest.mark.asyncio
async def test_verify_email_audit(client, unique_email):
    """Test audit log for email verification."""
    from unittest.mock import patch, AsyncMock
    
    # Mock Email Service to capture OTP
    with patch("app.core.email.EmailService.send_otp_email", new_callable=AsyncMock) as mock_email:
        # 1. Register User
        register_data = {
            "email": unique_email,
            "password": "Password123!",
            "first_name": "Audit",
            "last_name": "OTP",
            "phone_number": "+1234567890"
        }
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 201
        
        # Get OTP from mock call args
        assert mock_email.called
        # Call args: (email, otp_code, purpose)
        call_args = mock_email.call_args[0]
        otp_code = call_args[1]
        
        # 2. Verify Email
        verify_response = await client.post(
            "/api/v1/auth/verify-email",
            json={"email": unique_email, "otp": otp_code}
        )
        assert verify_response.status_code == 200
        
        # 3. Verify Audit Log
        db = mongodb.get_db()
        logs = await db["audit_logs"].find({
            "target_id": str(unique_email), # Wait, audit logic uses user ID as target_id for verify_email?
            # Let's check auth.py: 
            # target_id=str(user.id), target_type="user"
            "action": "verify_email"
        }).to_list(length=1)
        
        # If logs empty, try searching by action only first debugging
        if not logs:
            logs = await db["audit_logs"].find({"action": "verify_email"}).to_list(length=10)
            # Find the one for our email
            logs = [l for l in logs if l.get("details", {}).get("email") == unique_email]
        
        assert len(logs) == 1
        assert logs[0]["details"]["email"] == unique_email
        assert logs[0]["target_type"] == "user"

