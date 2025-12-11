"""
Tests for Admin and Customer Management with Soft Delete and Audit Logging.
"""
import pytest
from uuid import uuid4
from sqlmodel import select
from app.modules.users.models import User, Admin, Customer
from app.modules.users.service import UserManagementService
from app.modules.users.schemas import AdminCreate, CustomerCreate, AdminUpdate, CustomerUpdate
from app.core.mongo import mongodb

@pytest.fixture
def service(session):
    return UserManagementService(session)

@pytest.fixture
def super_admin_id():
    return uuid4()

@pytest.fixture(autouse=True)
async def setup_mongo_connection():
    """Ensure MongoDB connection is active for tests."""
    mongodb.connect()
    # Clear audit logs
    db = mongodb.get_db()
    await db["audit_logs"].delete_many({})
    yield
    await db["audit_logs"].delete_many({})
    mongodb.close()

@pytest.mark.asyncio
async def test_create_admin(service, super_admin_id):
    """Test creating an admin."""
    data = AdminCreate(email="newadmin@test.com", password="password123", username="newadmin")
    admin = await service.create_admin(data, actor_id=super_admin_id)
    
    assert admin.username == "newadmin"
    assert admin.email == "newadmin@test.com"
    assert admin.is_active is True
    
    # Verify User created
    from app.modules.users.repository import UserRepository
    user_repo = UserRepository(service.session)
    user = await user_repo.get_by_email("newadmin@test.com")
    assert user is not None
    assert user.user_type == "ADMIN"

@pytest.mark.asyncio
async def test_soft_delete_and_resuse_email_admin(service, super_admin_id):
    """Test soft delete and email reuse for admin."""
    # 1. Create
    data = AdminCreate(email="reuse@test.com", password="password123", username="reuseuser")
    admin = await service.create_admin(data, actor_id=super_admin_id)
    
    # 2. Delete
    await service.delete_admin(admin.id, actor_id=super_admin_id)
    
    # 3. Verify Soft Deleted (List should not return it)
    admins, _ = await service.list_admins()
    assert not any(a.id == admin.id for a in admins)
    
    # Verify in DB directly
    from app.modules.users.repository import UserRepository
    user_repo = UserRepository(service.session)
    user = await user_repo.get(admin.user_id)
    assert user.is_active is False
    assert user.deleted_at is not None
    assert user.email.startswith("deleted_")
    assert "reuse@test.com" in user.email
    
    # 4. Re-create with same email
    data2 = AdminCreate(email="reuse@test.com", password="newpassword123", username="reuseuser2")
    admin2 = await service.create_admin(data2, actor_id=super_admin_id)
    
    assert admin2.email == "reuse@test.com"
    assert admin2.username == "reuseuser2"
    assert admin2.is_active is True
    assert admin2.id != admin.id

@pytest.mark.asyncio
async def test_create_customer_audit_log(service, super_admin_id):
    """Test customer creation and audit log entry."""
    data = CustomerCreate(email="audit@test.com", password="password123", first_name="Audit", last_name="Log")
    customer = await service.create_customer(data, actor_id=super_admin_id)
    
    # Verify Mongo Audit Log
    db = mongodb.get_db()
    logs = await db["audit_logs"].find({"target_id": str(customer.id), "action": "create_customer"}).to_list(length=1)
    
    assert len(logs) == 1
    log = logs[0]
    assert log["actor_id"] == str(super_admin_id)
    assert log["target_type"] == "customer"
    assert log["details"]["email"] == "audit@test.com"

@pytest.mark.asyncio
async def test_update_customer(service, super_admin_id):
    """Test updating customer."""
    # Create
    data = CustomerCreate(email="update@test.com", password="password123", first_name="Old", last_name="Name")
    customer = await service.create_customer(data, actor_id=super_admin_id)
    
    # Update
    update_data = CustomerUpdate(first_name="New", last_name="Name")
    updated = await service.update_customer(customer.id, update_data, actor_id=super_admin_id)
    
    assert updated.first_name == "New"
    
    # Verify Audit Log
    db = mongodb.get_db()
    logs = await db["audit_logs"].find({"target_id": str(customer.id), "action": "update_customer"}).to_list(length=1)
    assert len(logs) == 1
    assert logs[0]["old_values"]["first_name"] == "Old"
    assert logs[0]["new_values"]["first_name"] == "New"

@pytest.mark.asyncio
async def test_list_customers_filtering(service, super_admin_id):
    """Test filtering, searching, and sorting customers."""
    # Create test data
    c1 = await service.create_customer(
        CustomerCreate(email="alice@filtering-test.com", password="password123", first_name="Alice", last_name="A", phone_number="111"), 
        actor_id=super_admin_id
    )
    c2 = await service.create_customer(
        CustomerCreate(email="bob@filtering-test.com", password="password123", first_name="Bob", last_name="B", phone_number="222"), 
        actor_id=super_admin_id
    )
    c3 = await service.create_customer(
        CustomerCreate(email="charlie@filtering-test.com", password="password123", first_name="Charlie", last_name="C", phone_number="333"), 
        actor_id=super_admin_id
    )
    
    # 1. Test Filter (User email)
    items, total = await service.list_customers(filters={"email": "alice@filtering-test.com"})
    assert total == 1
    assert items[0].email == "alice@filtering-test.com"
    
    # 2. Test Filter (Customer first_name)
    items, total = await service.list_customers(filters={"first_name": "Bob"})
    assert total >= 1
    assert items[0].first_name == "Bob"
    
    # 3. Test Search (Combined fields)
    items, total = await service.list_customers(search_query="filtering-test")
    # Should match all 3
    assert total == 3
    
    # Search "111" -> Alice
    items, total = await service.list_customers(search_query="111")
    assert total == 1
    assert items[0].first_name == "Alice"
    
    # 4. Test Sorting (Filter to our subset first)
    filters = {"email__like": "filtering-test"}
    
    # Descending (default created_at) - C, B, A
    items, _ = await service.list_customers(filters=filters, sort_by="first_name", sort_order="desc")
    assert items[0].first_name == "Charlie"
    
    # Ascending
    items, _ = await service.list_customers(filters=filters, sort_by="first_name", sort_order="asc")
    assert items[0].first_name == "Alice"

@pytest.mark.asyncio
async def test_list_admins_filtering(service, super_admin_id):
    """Test filtering, searching, and sorting admins."""
    import uuid
    uid = str(uuid.uuid4())[:8]
    email1 = f"alice_{uid}@filtering-test.com"
    email2 = f"bob_{uid}@filtering-test.com"
    
    # Create test admins
    # Note: create_admin takes AdminCreate which uses username/email
    a1 = await service.create_admin(
        AdminCreate(email=email1, password="password123", username=f"alice_{uid}"), 
        actor_id=super_admin_id
    )
    a2 = await service.create_admin(
        AdminCreate(email=email2, password="password123", username=f"bob_{uid}"), 
        actor_id=super_admin_id
    )
    
    # 1. Test Filter (User email)
    items, total = await service.list_admins(filters={"email": email1})
    assert total == 1
    assert items[0].email == email1
    
    # 2. Test Filter (Admin username)
    items, total = await service.list_admins(filters={"username": f"bob_{uid}"})
    assert total >= 1
    assert items[0].username == f"bob_{uid}"
    
    # 3. Test Search (Combined fields - e.g. email)
    items, total = await service.list_admins(search_query=f"filtering-test.com")
    # Should match both (and potentially others if string is common, but with unique emails it should be fine)
    # But since we search for "filtering-test.com", it matches both our new users.
    # To be safe, let's search for the unique UID part
    items, total = await service.list_admins(search_query=uid)
    assert total == 2
    
    # Search username
    items, total = await service.list_admins(search_query=f"alice_{uid}")
    assert total == 1
    assert items[0].username == f"alice_{uid}"
    
    # 4. Test Sorting (Filter to our subset first)
    filters = {"email__like": uid}
    
    # Descending (default created_at) - Bob (created 2nd), Alice (created 1st)
    # Actually created_at might be same second.
    # Let's sort by username
    items, _ = await service.list_admins(filters=filters, sort_by="username", sort_order="desc")
    assert items[0].username == f"bob_{uid}"
    
    # Ascending
    items, _ = await service.list_admins(filters=filters, sort_by="username", sort_order="asc")
    assert items[0].username == f"alice_{uid}"
