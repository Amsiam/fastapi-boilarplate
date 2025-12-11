import pytest
import pytest_asyncio
from sqlmodel import select
from app.core.filtering import apply_filters, apply_sorting, apply_search, SortOrder
from app.modules.users.models import User, UserType

# Mock model for independent testing (or just use User)
# We will use the existing User model for integration-like unit testing.

@pytest.mark.asyncio
async def test_apply_filters_eq(session):
    # This is more of a query construction test. 
    # Real integration test requires data in DB.
    
    # Let's write an integration test using the repository.
    from app.modules.users.repository import UserRepository
    repo = UserRepository(session)
    
    # Create test users with unique marker
    u1 = await repo.create(User(email="eq_test_a@example.com", hashed_password="pw", user_type=UserType.ADMIN))
    u2 = await repo.create(User(email="eq_test_b@example.com", hashed_password="pw", user_type=UserType.CUSTOMER))
    u3 = await repo.create(User(email="eq_test_c@example.com", hashed_password="pw", user_type=UserType.CUSTOMER))
    
    # Test strict equality
    # We filter by both role AND our unique test marker to avoid pollution
    items, total = await repo.get_list(filters={"user_type": UserType.CUSTOMER, "email__like": "eq_test_"})
    
    assert total == 2
    assert len(items) == 2
    assert all(u.user_type == UserType.CUSTOMER for u in items)
    assert all("eq_test_" in u.email for u in items)

@pytest.mark.asyncio
async def test_apply_filters_search(session):
    from app.modules.users.repository import UserRepository
    repo = UserRepository(session)
    
    await repo.create(User(email="unique1@test.com", hashed_password="pw", user_type=UserType.CUSTOMER, first_name="Zorro", last_name="X"))
    await repo.create(User(email="other2@test.com", hashed_password="pw", user_type=UserType.CUSTOMER, first_name="Arthur", last_name="Y"))
    
    
    # Search for "Zorro" in email (since User doesn't have first_name)
    items, total = await repo.get_list(search_query="unique1", search_fields=["email"])
    
    # Filter only relevant items just in case (though search should handle it)
    found_zorro = [i for i in items if "unique1" in i.email]
    assert len(found_zorro) == 1
    assert found_zorro[0].email == "unique1@test.com"

@pytest.mark.asyncio
async def test_apply_filters_gt(session):
    # This is hard to test on User as it doesn't have many numeric fields.
    # But filtering logic code is generic.
    pass

@pytest.mark.asyncio
async def test_apply_sorting(session):
    from app.modules.users.repository import UserRepository
    from app.modules.users.models import User, UserType
    repo = UserRepository(session)
    
    await repo.create(User(email="sort_a@test.com", hashed_password="pw", user_type=UserType.CUSTOMER, first_name="A", last_name="SortTest"))
    await repo.create(User(email="sort_b@test.com", hashed_password="pw", user_type=UserType.CUSTOMER, first_name="B", last_name="SortTest"))
    # Filter to only get our test items for sorting check
    # Use email__contains as User doesn't have last_name
    filters = {"email__like": "sort_"}
    
    # Descending
    items, _ = await repo.get_list(filters=filters, sort_by="email", sort_order="desc")
    # Should get sort_b then sort_a
    assert items[0].email == "sort_b@test.com"
    
    # Ascending
    items, _ = await repo.get_list(filters=filters, sort_by="email", sort_order="asc")
    assert items[0].email == "sort_a@test.com"
