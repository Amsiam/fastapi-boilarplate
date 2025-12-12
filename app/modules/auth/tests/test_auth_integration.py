import pytest
from httpx import AsyncClient
from uuid import uuid4
from app.modules.users.models import User, Admin
from app.core.security import get_password_hash
from app.constants.enums import UserType
from app.modules.roles.models import Role

@pytest.mark.asyncio
async def test_auth_integration(client: AsyncClient, session):
    """
    Integration tests for Authentication flows.
    """
    
    # 1. Setup Data
    # Create Role
    role = Role(name="AUTH_TEST_ROLE", description="Test Role", is_system=False)
    session.add(role)
    await session.commit()
    
    # Create Admin User
    password = "strongpassword123"
    admin_id = uuid4()
    admin_email = f"auth_admin_{uuid4()}@example.com"
    admin_user = User(
        id=admin_id,
        email=admin_email,
        hashed_password=get_password_hash(password),
        user_type=UserType.ADMIN,
        is_active=True,
        is_verified=True
    )
    session.add(admin_user)
    
    # Create Admin Profile
    admin_profile = Admin(
        user_id=admin_id,
        username=f"admin_{uuid4().hex[:8]}",
        role_id=role.id
    )
    session.add(admin_profile)
    await session.commit()
    
    # 2. Login
    login_data = {
        "username": admin_email, # OAuth2PasswordRequestForm uses 'username' field for email usually
        "password": password
    }
    # Note: /api/v1/auth/access-token is usually the endpoint
    # Check endpoints.py path. Assuming /api/v1/auth/login or /api/v1/oauth/token
    # Let's check endpoints.py, but for now try /api/v1/auth/login (standard in this project?)
    # or /auth/access-token if using OAuth2 standard path.
    # Looking at directory: app/modules/auth/endpoints.py
    
    # It is likely /api/v1/auth/login. Endpoint expects JSON.
    res = await client.post("/api/v1/auth/login", json=login_data)

    assert res.status_code == 200, f"Login failed: {res.text}"
    token_data = res.json()["data"]
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    
    # 3. Get Current User (Me)
    headers = {"Authorization": f"Bearer {access_token}"}
    res = await client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    user_data = res.json()["data"]
    assert user_data["email"] == admin_email
    assert user_data["user_type"] == "ADMIN"
    
    # 4. Refresh Token
    # Endpoint expects refresh_token in POST Body (JSON).
    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    
    assert res.status_code == 200, f"Refresh failed: {res.text}"
    new_token_data = res.json()["data"]
    assert "access_token" in new_token_data
    assert new_token_data["access_token"] != access_token
    
    # 5. Logout (if exists)
    # res = await client.post("/api/v1/auth/logout", headers=headers)
    # assert res.status_code == 200
    
    # 6. Invalid Login
    bad_data = {
        "username": admin_email,
        "password": "wrongpassword"
    }
    res = await client.post("/api/v1/auth/login", json=bad_data)
    assert res.status_code == 401 or res.status_code == 400


@pytest.mark.asyncio
async def test_full_auth_flow(client: AsyncClient, session):
    """
    Test complete user lifecycle: Register -> Verify -> Login -> Change Password.
    """
    from app.core.security import generate_otp, hash_otp
    from app.core.cache import otp_key, set_cache
    from app.constants.enums import OTPType
    
    email = f"customer_{uuid4()}@example.com"
    password = "CustomerPass123!"
    
    # 1. Register
    reg_data = {
        "email": email,
        "password": password,
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890"
    }
    res = await client.post("/api/v1/auth/register", json=reg_data)
    assert res.status_code == 201, f"Register failed: {res.text}"
    
    # 2. Try Login (Should fail - Email not verified)
    login_data = {"username": email, "password": password}
    res = await client.post("/api/v1/auth/login", json=login_data)
    assert res.status_code == 401, f"Should fail verification: {res.text}"
    assert "AUTH_002" in res.text or "verify" in res.text.lower()
    
    # 3. Verify Email
    # In integration test, we simulate OTP by setting it in cache (simulating email send + user reading it)
    # OR we can Mock encryption. But we need to match what the service generated.
    # Service generated a random OTP. We can't easy guess it.
    # We can OVERRIDE the OTP in cache with our own known OTP.
    
    known_otp = "123456"
    otp_hash = hash_otp(known_otp)
    
    cache_key = otp_key(email, OTPType.EMAIL_VERIFICATION.value)
    
    # Manually inject known OTP into Redis (via cache helper)
    # We assume Integration Test environment has working Redis Connection.
    # The `otp_service` stores it as a dict.
    from datetime import datetime
    otp_data = {
        "hash": otp_hash,
        "attempts": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # We need to await set_cache.
    # set_cache is async.
    await set_cache(cache_key, otp_data, expire=600)
    
    verify_data = {"email": email, "otp": known_otp}
    res = await client.post("/api/v1/auth/verify-email", json=verify_data)
    assert res.status_code == 200, f"Verify failed: {res.text}"
    
    # 4. Login (Success)
    res = await client.post("/api/v1/auth/login", json=login_data)
    assert res.status_code == 200, f"Login failed: {res.text}"
    tokens = res.json()["data"]
    access_token = tokens["access_token"]
    
    # 5. Change Password
    new_password = "NewPassword123!"
    headers = {"Authorization": f"Bearer {access_token}"}
    change_pw_data = {
        "current_password": password,
        "new_password": new_password
    }
    res = await client.post("/api/v1/auth/change-password", json=change_pw_data, headers=headers)
    assert res.status_code == 200, f"Change password failed: {res.text}"
    
    # 6. Login with Old Password (Fail)
    res = await client.post("/api/v1/auth/login", json=login_data)
    assert res.status_code == 401
    
    # 7. Login with New Password (Success)
    new_login_data = {"username": email, "password": new_password}
    res = await client.post("/api/v1/auth/login", json=new_login_data)
    assert res.status_code == 200
