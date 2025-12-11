import pytest
import uuid
import asyncio
from datetime import datetime, timedelta
from app.modules.audit.service import audit_service
from app.modules.audit.models import AuditLog

@pytest.mark.asyncio
async def test_audit_filtering_logic():
    """Test standard filtering, operator filtering, search, and sort."""
    
    # 1. Setup Data
    actor_id = uuid.uuid4()
    
    # Create logs with different timestamps and actions
    # Log 1: "login" - 1 hour ago
    await audit_service.log_action(
        action="login",
        actor_id=actor_id,
        target_type="auth",
        details={"method": "password"}
    )
    # Hack: We need to manipulate the timestamp, but log_action uses utcnow().
    # We'll insert directly or we can just assume timestamps are close and test other fields first.
    # For timestamp filtering, we really should insert manually into collection to control time.
    
    from app.core.mongo import mongodb
    db = mongodb.get_db()
    collection = db["audit_logs"]
    
    # Clear collection for this test to avoid noise? 
    # Or just use unique actor_id to filter our view.
    
    # Let's insert manually to control timestamps
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    
    log1 = {
        "action": "create_user",
        "actor_id": str(actor_id),
        "target_type": "user",
        "timestamp": yesterday,
        "details": {"email": "old@test.com"}
    }
    log2 = {
        "action": "delete_user",
        "actor_id": str(actor_id),
        "target_type": "user",
        "timestamp": now,
        "details": {"email": "new@test.com"}
    }
    log3 = {
        "action": "update_role",
        "actor_id": str(actor_id),
        "target_type": "role",
        "timestamp": now,
        "details": {"name": "Admin"}
    }
    
    await collection.insert_many([log1, log2, log3])
    
    # 2. Test Filters
    
    # Exact Match
    logs, total = await audit_service.list_logs(filters={"action": "create_user", "actor_id": str(actor_id)})
    assert total == 1
    assert logs[0]["action"] == "create_user"
    
    # Operator: timestamp__gt (Greater than yesterday - 1 hour)
    # Should get log2 and log3
    check_time = yesterday + timedelta(hours=1)
    logs, total = await audit_service.list_logs(
        filters={
            "timestamp__gt": check_time, 
            "actor_id": str(actor_id)
        }
    )
    assert total == 3
    actions = [l["action"] for l in logs]
    assert "delete_user" in actions
    assert "update_role" in actions
    
    # Operator: IN
    logs, total = await audit_service.list_logs(
        filters={
            "action__in": ["create_user", "update_role"],
            "actor_id": str(actor_id)
        }
    )
    assert total == 2
    
    # 3. Test Search
    # Search for "old@test.com" (in details)
    logs, total = await audit_service.list_logs(
        search_query="old@test.com",
        filters={"actor_id": str(actor_id)}
    )
    assert total == 1
    assert logs[0]["action"] == "create_user"
    
    # Search for "user" (matches target_type="user" or action="...user")
    logs, total = await audit_service.list_logs(
        search_query="user",
        filters={"actor_id": str(actor_id)}
    )
    assert total == 2 # create_user, delete_user
    
    # 4. Test Sorting
    # Sort by action ASC
    logs, total = await audit_service.list_logs(
        filters={"actor_id": str(actor_id)},
        sort_by="action",
        sort_order="asc"
    )
    assert logs[0]["action"] == "create_user"
    assert logs[1]["action"] == "delete_user"
    assert logs[2]["action"] == "login"
    assert logs[3]["action"] == "update_role"
    
    # Sort by timestamp DESC (default)
    # log2 ("delete_user"), log3 ("update_role"), log_login ("login") are "now".
    # log1 ("create_user") is yesterday.
    # log2 and log3 are "now", log1 is yesterday.
    # log2 and log3 order might be indeterminate if same millisecond, but query should return them before log1
    logs, total = await audit_service.list_logs(
        filters={"actor_id": str(actor_id)},
        sort_by="timestamp",
        sort_order="desc"
    )
    assert logs[-1]["action"] == "create_user" # Last one should be the oldest
    
