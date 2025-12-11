import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_sqli_create_role(client: AsyncClient):
    """
    Test SQLi payload in Role name and description.
    """
    payload = {
        "name": "SuperAdmin'--",
        "description": "Exploit' UNION SELECT 1,2,3 --",
        "permission_ids": []
    }
    response = await client.post("/api/v1/admin/roles", json=payload)
    
    # Should be 401/403/422/201. Should NOT be 500.
    assert response.status_code in [401, 403, 422, 201]

@pytest.mark.asyncio
async def test_sqli_role_id_path(client: AsyncClient):
    """
    Test SQLi via path parameter (UUID injection).
    FastAPI validation should reject non-UUID strings immediately.
    """
    # Payload: /api/v1/admin/roles/' OR '1'='1
    response = await client.get("/api/v1/admin/roles/' OR '1'='1")
    
    # Validation error (422), Not Found (404), or Unauthorized (401)
    assert response.status_code in [422, 404, 401]
