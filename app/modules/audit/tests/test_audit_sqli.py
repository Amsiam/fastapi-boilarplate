import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_sqli_audit_query_params(client: AsyncClient):
    """
    Test NoSQLi/SQLi in query parameters for audit logs.
    """
    # ?action={"$ne": null}
    response = await client.get("/api/v1/admin/audit-logs/?action={\"$ne\": null}")
    assert response.status_code in [401, 403, 422]
