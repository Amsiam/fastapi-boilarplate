"""
Auth Service tests.
"""
import pytest
from uuid import uuid4
from sqlmodel import select

from app.modules.auth.service import AuthService
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.constants.enums import UserType
from app.modules.users.models import User, Customer
from app.core.security import hash_password, generate_otp, hash_otp, verify_otp
from app.core.mongo import mongodb

@pytest.fixture(autouse=True)
async def setup_mongo_connection():
    """Ensure MongoDB connection is active for tests."""
    mongodb.connect()
    yield
    mongodb.close()

class TestAuthService:
    """Test AuthService with real database."""
    
    async def test_auth_service_init(self, session):
        """Test AuthService initialization."""
        service = AuthService(session)
        assert service.db is session
    
    async def test_authenticate_user_not_found(self, session):
        """Test authentication with non-existent user."""
        service = AuthService(session)
        
        with pytest.raises(AuthenticationError):
            await service.authenticate_user("nonexistent@example.com", "password")
    
    async def test_authenticate_user_success(self, session):
        """Test successful authentication."""
        # Create a test user
        user = User(
            email="auth_test@example.com",
            hashed_password=hash_password("testpassword123"),
            first_name="Auth",
            last_name="Test",
            is_active=True,
            is_verified=True,
            user_type=UserType.CUSTOMER
        )
        session.add(user)
        await session.commit()
        
        service = AuthService(session)
        authenticated_user = await service.authenticate_user("auth_test@example.com", "testpassword123")
        
        assert authenticated_user.email == "auth_test@example.com"
    
    async def test_authenticate_user_wrong_password(self, session):
        """Test authentication with wrong password."""
        # Create a test user
        user = User(
            email="wrong_pass_test@example.com",
            hashed_password=hash_password("correctpassword"),
            first_name="Wrong",
            last_name="Pass",
            is_active=True,
            is_verified=True,
            user_type=UserType.CUSTOMER
        )
        session.add(user)
        await session.commit()
        
        service = AuthService(session)
        
        with pytest.raises(AuthenticationError):
            await service.authenticate_user("wrong_pass_test@example.com", "wrongpassword")
    
    async def test_authenticate_user_inactive(self, session):
        """Test authentication with inactive user."""
        user = User(
            email="inactive_test@example.com",
            hashed_password=hash_password("testpassword123"),
            first_name="Inactive",
            last_name="User",
            is_active=False,
            is_verified=True,
            user_type=UserType.CUSTOMER
        )
        session.add(user)
        await session.commit()
        
        service = AuthService(session)
        
        with pytest.raises(AuthenticationError):
            await service.authenticate_user("inactive_test@example.com", "testpassword123")
    
    async def test_register_customer_success(self, session):
        """Test successful customer registration."""
        service = AuthService(session)
        
        user = await service.register_customer(
            email="newcustomer@example.com",
            password="securepassword123",
            first_name="New",
            last_name="Customer"
        )
        
        assert user.email == "newcustomer@example.com"
        assert user.user_type == UserType.CUSTOMER
        
        # Verify customer profile
        result = await session.execute(select(Customer).where(Customer.user_id == user.id))
        customer = result.scalar_one()
        assert customer.first_name == "New"
        assert customer.last_name == "Customer"
    
    async def test_register_customer_duplicate(self, session):
        """Test registering customer with duplicate email."""
        # Create existing user
        user = User(
            email="duplicate@example.com",
            hashed_password=hash_password("password123"),
            first_name="Existing",
            last_name="User",
            is_active=True,
            user_type=UserType.CUSTOMER
        )
        session.add(user)
        await session.commit()
        
        service = AuthService(session)
        
        with pytest.raises(ConflictError):
            await service.register_customer(
                email="duplicate@example.com",
                password="password123",
                first_name="Test",
                last_name="User"
            )
    
    async def test_reset_password_user_not_found(self, session):
        """Test reset password for non-existent user."""
        service = AuthService(session)
        
        with pytest.raises(NotFoundError):
            await service.reset_password("nonexistent@example.com", "newpassword")


class TestOTPFunctions:
    """Test OTP-related functions."""
    
    async def test_generate_otp_format(self):
        """Test that generated OTP has correct format."""
        otp = generate_otp()
        assert len(otp) == 6
        assert otp.isdigit()
    
    async def test_otp_hashing(self):
        """Test OTP hashing and verification."""
        otp = generate_otp()
        hashed = hash_otp(otp)
        
        # Correct OTP should verify
        assert verify_otp(otp, hashed) is True
        
        # Wrong OTP should not verify
        assert verify_otp("000000", hashed) is False
