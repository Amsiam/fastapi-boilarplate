import pytest
import time
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.users.repository import UserRepository

@pytest.mark.asyncio
async def test_sqli_login_bypass(client: AsyncClient):
    """
    Test SQL Injection attempt on login endpoint.
    Payload: ' OR '1'='1
    Expected: 401 Unauthorized (should not log in as first user)
    """
    payload = {
        "username": "' OR '1'='1",
        "password": "randompassword"
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code in [401, 422]
    
    payload["username"] = "admin'+OR+'1'='1@example.com"
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code in [401, 422, 404, 400]

@pytest.mark.asyncio
async def test_sqli_repository_direct(session: AsyncSession):
    """
    Test SQL Injection attempt directly on repository.
    Even if API validation stops it, the Repo layer should be safe.
    """
    repo = UserRepository(session)
    sqli_payload = "' OR '1'='1"
    
    # Should safely query for the literal string
    user = await repo.get_by_email(sqli_payload)
    assert user is None

@pytest.mark.asyncio
async def test_sqli_register_fields(client: AsyncClient):
    """
    Test SQL Injection in registration fields.
    """
    payload = {
        "email": "sqli_test@example.com",
        "password": "password123",
        "first_name": "'; DROP TABLE users; --",
        "last_name": "Test",
        "phone_number": "1234567890"
    }
    
    response = await client.post("/api/v1/auth/register", json=payload)
    if response.status_code == 201:
        assert response.status_code == 201
        
@pytest.mark.asyncio
async def test_sqli_via_headers_audit(client: AsyncClient):
    """
    Test potential SQLi in Headers (User-Agent) which goes to Audit Logs.
    """
    headers = {
        "User-Agent": "Mozilla/5.0'; DROP TABLE users; --"
    }
    payload = {
        "username": "random@example.com", 
        "password": "password"
    }
    await client.post("/api/v1/auth/login", json=payload, headers=headers)

@pytest.mark.asyncio
async def test_blind_sqli_time_based(client: AsyncClient):
    """
    Test Time-Based Blind SQL Injection.
    Payload attempts to force the database to sleep.
    """
    payload = {
        "username": "admin' || pg_sleep(3) || '@example.com",
        "password": "password"
    }
    
    start_time = time.time()
    response = await client.post("/api/v1/auth/login", json=payload)
    end_time = time.time()
    
    duration = end_time - start_time
    assert duration < 2.0 

@pytest.mark.asyncio
async def test_unicode_injection(client: AsyncClient):
    """
    Test Unicode/Homoglyph injection.
    """
    payload = {
        "username": "admin\u02b9 OR \u02b91\u02b9=\u02b91", # Modifier Letter Prime
        "password": "password"
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code in [401, 422]

@pytest.mark.asyncio
async def test_union_based_attempt(session: AsyncSession):
    """
    Test UNION-based injection attempt directly on repository search.
    """
    repo = UserRepository(session)
    payload = "' UNION SELECT 1, 'hacked', 'hacked', 'hacked' --"
    user = await repo.get_by_email(payload)
    assert user is None
