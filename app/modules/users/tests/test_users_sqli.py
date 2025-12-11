import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_sqli_create_customer(client: AsyncClient, session: AsyncSession):
    """
    Test SQLi payload in customer creation fields (Admin context).
    Need to be admin to call this.
    """
    payload = {
        "email": "customer_sqli@example.com",
        "password": "password123",
        "first_name": "' OR 1=1; --",
        "last_name": "Smith",
        "phone_number": "123"
    }
    
    response = await client.post("/api/v1/admin/customers/", json=payload)
    # Without auth token, this should be 401/403. 
    # Validates that injection doesn't crash the checking logic.
    assert response.status_code in [401, 403, 422, 201]
