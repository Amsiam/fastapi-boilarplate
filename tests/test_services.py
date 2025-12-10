"""
Service layer integration tests using test database.
Run with: pytest tests/test_services.py -v
"""
import pytest
from uuid import uuid4

from app.services.auth_service import AuthService
from app.services.oauth_service import OAuthService
from app.services.role_service import RoleService, PermissionService
from app.services.oauth_provider_service import OAuthProviderService
from app.core.exceptions import (
    AuthenticationError, 
    ConflictError, 
    NotFoundError
)
from app.constants.enums import UserRole
from app.models.user import User
from app.models.oauth import OAuthProvider
from app.models.role import Role, Permission
from app.core.security import hash_password


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
            role=UserRole.CUSTOMER
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
            role=UserRole.CUSTOMER
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
            role=UserRole.CUSTOMER
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
        assert user.role == UserRole.CUSTOMER
        
        # Verify customer profile
        from sqlmodel import select
        from app.models.user import Customer
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
            role=UserRole.CUSTOMER
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


class TestOAuthService:
    """Test OAuthService with real database."""
    
    async def test_oauth_service_init(self, session):
        """Test OAuthService initialization."""
        service = OAuthService(session)
        assert service.db is session
    
    async def test_list_providers_empty(self, session):
        """Test listing providers when none exist."""
        service = OAuthService(session)
        providers = await service.list_providers()
        # Result could be empty or have providers depending on test order
        assert isinstance(providers, list)
    
    async def test_list_providers_only_active(self, session):
        """Test listing providers returns only active ones."""
        # Create active and inactive providers
        active_provider = OAuthProvider(
            name="active_test_provider",
            display_name="Active Test",
            client_id="client123",
            client_secret="secret123",
            authorization_url="https://auth.example.com",
            token_url="https://token.example.com",
            user_info_url="https://userinfo.example.com",
            is_active=True
        )
        inactive_provider = OAuthProvider(
            name="inactive_test_provider",
            display_name="Inactive Test",
            client_id="client456",
            client_secret="secret456",
            authorization_url="https://auth2.example.com",
            token_url="https://token2.example.com",
            user_info_url="https://userinfo2.example.com",
            is_active=False
        )
        session.add(active_provider)
        session.add(inactive_provider)
        await session.commit()
        
        service = OAuthService(session)
        providers = await service.list_providers()
        
        # Should only include active providers
        provider_names = [p["name"] for p in providers]
        assert "active_test_provider" in provider_names
        assert "inactive_test_provider" not in provider_names
    
    async def test_get_login_url_provider_not_found(self, session):
        """Test getting login URL for non-existent provider."""
        service = OAuthService(session)
        
        with pytest.raises(NotFoundError):
            await service.get_login_url("nonexistent_provider", "http://callback")


class TestRoleService:
    """Test RoleService with real database."""
    
    async def test_role_service_init(self, session):
        """Test RoleService initialization."""
        service = RoleService(session)
        assert service.db is session
    
    async def test_create_role_success(self, session):
        """Test successful role creation."""
        service = RoleService(session)
        
        role = await service.create_role(
            name="test_role_" + str(uuid4())[:8],
            description="Test role description"
        )
        
        assert role is not None
        assert "test_role_" in role["name"]
    
    async def test_create_role_duplicate(self, session):
        """Test creating role with duplicate name."""
        role_name = "duplicate_role_" + str(uuid4())[:8]
        
        # Create first role
        role = Role(name=role_name, description="First role")
        session.add(role)
        await session.commit()
        
        service = RoleService(session)
        
        with pytest.raises(ConflictError):
            await service.create_role(name=role_name, description="Duplicate role")
    
    async def test_get_role_not_found(self, session):
        """Test getting non-existent role."""
        service = RoleService(session)
        
        with pytest.raises(NotFoundError):
            await service.get_role(uuid4())
    
    async def test_list_roles_paginated(self, session):
        """Test listing roles with pagination."""
        service = RoleService(session)
        
        result = await service.list_roles(page=1, per_page=10)
        
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "per_page" in result


class TestPermissionService:
    """Test PermissionService with real database."""
    
    async def test_permission_service_init(self, session):
        """Test PermissionService initialization."""
        service = PermissionService(session)
        assert service.db is session
    
    async def test_create_permission_success(self, session):
        """Test successful permission creation."""
        service = PermissionService(session)
        
        permission = await service.create_permission(
            code="test_permission_" + str(uuid4())[:8],
            description="Test permission"
        )
        
        assert permission is not None
        assert "test_permission_" in permission["code"]
    
    async def test_list_permissions(self, session):
        """Test listing permissions."""
        service = PermissionService(session)
        
        permissions = await service.list_permissions()
        
        assert isinstance(permissions, list)


class TestOAuthProviderService:
    """Test OAuthProviderService with real database."""
    
    async def test_oauth_provider_service_init(self, session):
        """Test OAuthProviderService initialization."""
        service = OAuthProviderService(session)
        assert service.db is session
    
    async def test_create_provider_success(self, session):
        """Test successful provider creation."""
        service = OAuthProviderService(session)
        
        provider_name = "test_provider_" + str(uuid4())[:8]
        result = await service.create_provider(
            name=provider_name,
            display_name="Test Provider",
            client_id="client123",
            client_secret="secret123",
            authorization_url="https://auth.example.com",
            token_url="https://token.example.com",
            user_info_url="https://userinfo.example.com"
        )
        
        assert result["name"] == provider_name
        assert result["display_name"] == "Test Provider"
        assert result["is_active"] is True
    
    async def test_create_provider_duplicate(self, session):
        """Test creating provider with duplicate name."""
        provider_name = "duplicate_provider_" + str(uuid4())[:8]
        
        # Create first provider
        provider = OAuthProvider(
            name=provider_name,
            display_name="First Provider",
            client_id="client123",
            client_secret="secret123",
            authorization_url="https://auth.example.com",
            token_url="https://token.example.com",
            user_info_url="https://userinfo.example.com"
        )
        session.add(provider)
        await session.commit()
        
        service = OAuthProviderService(session)
        
        with pytest.raises(ConflictError):
            await service.create_provider(
                name=provider_name,
                display_name="Duplicate Provider",
                client_id="client456",
                client_secret="secret456",
                authorization_url="https://auth2.example.com",
                token_url="https://token2.example.com",
                user_info_url="https://userinfo2.example.com"
            )
    
    async def test_get_provider_success(self, session):
        """Test getting an existing provider."""
        # Create a provider
        provider = OAuthProvider(
            name="get_test_provider_" + str(uuid4())[:8],
            display_name="Get Test Provider",
            client_id="client123",
            client_secret="secret123",
            authorization_url="https://auth.example.com",
            token_url="https://token.example.com",
            user_info_url="https://userinfo.example.com"
        )
        session.add(provider)
        await session.commit()
        await session.refresh(provider)
        
        service = OAuthProviderService(session)
        result = await service.get_provider(provider.id)
        
        assert result["id"] == str(provider.id)
        assert result["display_name"] == "Get Test Provider"
    
    async def test_get_provider_not_found(self, session):
        """Test getting non-existent provider."""
        service = OAuthProviderService(session)
        
        with pytest.raises(NotFoundError):
            await service.get_provider(uuid4())
    
    async def test_list_providers_paginated(self, session):
        """Test listing providers with pagination."""
        service = OAuthProviderService(session)
        
        result = await service.list_providers(page=1, per_page=10)
        
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "per_page" in result
    
    async def test_update_provider_status(self, session):
        """Test updating provider status."""
        # Create a provider
        provider = OAuthProvider(
            name="status_test_provider_" + str(uuid4())[:8],
            display_name="Status Test Provider",
            client_id="client123",
            client_secret="secret123",
            authorization_url="https://auth.example.com",
            token_url="https://token.example.com",
            user_info_url="https://userinfo.example.com",
            is_active=True
        )
        session.add(provider)
        await session.commit()
        await session.refresh(provider)
        
        service = OAuthProviderService(session)
        
        # Deactivate
        result = await service.update_status(provider.id, False)
        assert result["is_active"] is False
        
        # Verify in database
        await session.refresh(provider)
        assert provider.is_active is False
        
        # Reactivate
        result = await service.update_status(provider.id, True)
        assert result["is_active"] is True
    
    async def test_update_provider_status_not_found(self, session):
        """Test updating status of non-existent provider."""
        service = OAuthProviderService(session)
        
        with pytest.raises(NotFoundError):
            await service.update_status(uuid4(), False)
    
    async def test_delete_provider_success(self, session):
        """Test successful provider deletion."""
        # Create a provider without linked accounts
        provider = OAuthProvider(
            name="delete_test_provider_" + str(uuid4())[:8],
            display_name="Delete Test Provider",
            client_id="client123",
            client_secret="secret123",
            authorization_url="https://auth.example.com",
            token_url="https://token.example.com",
            user_info_url="https://userinfo.example.com"
        )
        session.add(provider)
        await session.commit()
        await session.refresh(provider)
        
        provider_id = provider.id
        
        service = OAuthProviderService(session)
        await service.delete_provider(provider_id)
        
        # Verify deletion
        with pytest.raises(NotFoundError):
            await service.get_provider(provider_id)
    
    async def test_delete_provider_not_found(self, session):
        """Test deleting non-existent provider."""
        service = OAuthProviderService(session)
        
        with pytest.raises(NotFoundError):
            await service.delete_provider(uuid4())


class TestOTPFunctions:
    """Test OTP-related functions."""
    
    async def test_generate_otp_format(self):
        """Test that generated OTP has correct format."""
        from app.core.security import generate_otp
        otp = generate_otp()
        assert len(otp) == 6
        assert otp.isdigit()
    
    async def test_otp_hashing(self):
        """Test OTP hashing and verification."""
        from app.core.security import generate_otp, hash_otp, verify_otp
        otp = generate_otp()
        hashed = hash_otp(otp)
        
        # Correct OTP should verify
        assert verify_otp(otp, hashed) is True
        
        # Wrong OTP should not verify
        assert verify_otp("000000", hashed) is False
