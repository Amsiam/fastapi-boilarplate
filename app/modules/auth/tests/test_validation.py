
import pytest
from httpx import AsyncClient
from app.core.schemas.response import ErrorCode

@pytest.mark.asyncio
class TestChangePasswordValidation:
    """Test validation error specificity in change password endpoint."""
    

    async def test_change_password_validation_flow(self, client: AsyncClient, session):
        """Full flow with user creation to ensure known password."""
        # 1. Register a user
        unique_email = "val_test@example.com"
        password = "OldPassword123!"
        
        # Register
        await client.post("/api/v1/auth/register", json={
            "email": unique_email,
            "password": password,
            "first_name": "Val",
            "last_name": "Test"
        })
        
        # We need to verify email to login (Customer)
        # Verify directly in DB using the injected session
        from app.modules.users.models import User
        from sqlmodel import select
        
        result = await session.execute(select(User).where(User.email == unique_email))
        user = result.scalar_one()
        user.is_verified = True
        session.add(user)
        await session.commit()
        await session.refresh(user)
            
        # Login
        login_res = await client.post("/api/v1/auth/login", json={
            "username": unique_email,
            "password": password
        })
        token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Test Invalid Current Password
        res_current = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "WrongPassword",
                "new_password": "NewPassword123!"
            },
            headers=headers
        )
        assert res_current.status_code == 422
        data_current = res_current.json()
        assert data_current["error"]["field"] == "current_password"
        
        # 3. Test Invalid New Password
        res_new = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": password,
                "new_password": "short"
            },
            headers=headers
        )
        assert res_new.status_code == 422
        data_new = res_new.json()
        # Pydantic validation error returns list of errors
        assert data_new["errors"][0]["field"] == "new_password"
