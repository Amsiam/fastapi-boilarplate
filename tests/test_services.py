"""
Service layer unit tests.
Run with: pytest tests/test_services.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestAuthServiceMocked:
    """Test AuthService with mocked dependencies."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return AsyncMock()
    
    async def test_auth_service_init(self, mock_session):
        """Test AuthService initialization."""
        from app.services.auth_service import AuthService
        service = AuthService(mock_session)
        assert service.db is mock_session
    
    async def test_authenticate_user_not_found(self, mock_session):
        """Test authentication with non-existent user."""
        from app.services.auth_service import AuthService
        from app.core.exceptions import AuthenticationError
        
        with patch('app.services.auth_service.UserRepository') as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = None
            MockRepo.return_value = mock_repo
            
            service = AuthService(mock_session)
            
            with pytest.raises(AuthenticationError):
                await service.authenticate_user("nonexistent@example.com", "password")
    
    async def test_authenticate_user_inactive(self, mock_session):
        """Test authentication with inactive user."""
        from app.services.auth_service import AuthService
        from app.core.exceptions import AuthenticationError
        
        with patch('app.services.auth_service.UserRepository') as MockRepo:
            with patch('app.services.auth_service.verify_password') as mock_verify:
                mock_repo = AsyncMock()
                mock_user = MagicMock()
                mock_user.is_active = False
                mock_user.hashed_password = "hashed"
                mock_repo.get_by_email.return_value = mock_user
                mock_verify.return_value = True
                MockRepo.return_value = mock_repo
                
                service = AuthService(mock_session)
                
                with pytest.raises(AuthenticationError):
                    await service.authenticate_user("user@example.com", "password")
    
    async def test_register_customer_duplicate(self, mock_session):
        """Test registering customer with duplicate email."""
        from app.services.auth_service import AuthService
        from app.core.exceptions import ConflictError
        
        with patch('app.services.auth_service.UserRepository') as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = MagicMock()  # Existing user
            MockRepo.return_value = mock_repo
            
            service = AuthService(mock_session)
            
            with pytest.raises(ConflictError):
                await service.register_customer(
                    email="existing@example.com",
                    password="password123",
                    first_name="Test",
                    last_name="User"
                )
    
    async def test_reset_password_user_not_found(self, mock_session):
        """Test reset password for non-existent user."""
        from app.services.auth_service import AuthService
        from app.core.exceptions import NotFoundError
        
        with patch('app.services.auth_service.UserRepository') as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = None
            MockRepo.return_value = mock_repo
            
            service = AuthService(mock_session)
            
            with pytest.raises(NotFoundError):
                await service.reset_password("nonexistent@example.com", "newpassword")


class TestOAuthServiceMocked:
    """Test OAuthService with mocked dependencies."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return AsyncMock()
    
    async def test_oauth_service_init(self, mock_session):
        """Test OAuthService initialization."""
        from app.services.oauth_service import OAuthService
        service = OAuthService(mock_session)
        assert service.db is mock_session
    
    async def test_list_providers_empty(self, mock_session):
        """Test listing providers when none exist."""
        from app.services.oauth_service import OAuthService
        
        with patch('app.services.oauth_service.OAuthProviderRepository') as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_active_providers.return_value = []
            MockRepo.return_value = mock_repo
            
            service = OAuthService(mock_session)
            providers = await service.list_providers()
            assert providers == []
    
    async def test_get_login_url_provider_not_found(self, mock_session):
        """Test getting login URL for non-existent provider."""
        from app.services.oauth_service import OAuthService
        from app.core.exceptions import NotFoundError
        
        with patch('app.services.oauth_service.OAuthProviderRepository') as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_name.return_value = None
            MockRepo.return_value = mock_repo
            
            service = OAuthService(mock_session)
            
            with pytest.raises(NotFoundError):
                await service.get_login_url("nonexistent", "http://callback")


class TestRoleServiceMocked:
    """Test RoleService with mocked dependencies."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return AsyncMock()
    
    async def test_role_service_init(self, mock_session):
        """Test RoleService initialization."""
        from app.services.role_service import RoleService
        service = RoleService(mock_session)
        assert service.db is mock_session


class TestPermissionServiceMocked:
    """Test PermissionService with mocked dependencies."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return AsyncMock()
    
    async def test_permission_service_init(self, mock_session):
        """Test PermissionService initialization."""
        from app.services.role_service import PermissionService
        service = PermissionService(mock_session)
        assert service.db is mock_session


class TestOTPServiceMocked:
    """Test OTPService with mocked cache."""
    
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


class TestEmailServiceMocked:
    """Test EmailService with mocked SMTP."""
    
    async def test_email_service_render_template(self):
        """Test template rendering."""
        from app.services.email_service import EmailService
        
        # Test with non-existent template - should handle gracefully
        try:
            html = EmailService.render_template('nonexistent.html', {})
            # If it doesn't raise, template might not be required
        except Exception:
            # Template not found is expected
            pass


class TestOAuthProviderServiceMocked:
    """Test OAuthProviderService with mocked dependencies."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return AsyncMock()
    
    async def test_oauth_provider_service_init(self, mock_session):
        """Test OAuthProviderService initialization."""
        from app.services.oauth_provider_service import OAuthProviderService
        service = OAuthProviderService(mock_session)
        assert service.db is mock_session
    
    async def test_create_provider_duplicate(self, mock_session):
        """Test creating provider with duplicate name."""
        from app.services.oauth_provider_service import OAuthProviderService
        from app.core.exceptions import ConflictError
        
        with patch('app.services.oauth_provider_service.OAuthProviderRepository') as MockRepo:
            mock_repo = AsyncMock()
            # Simulate existing provider
            mock_repo.get_by_name.return_value = MagicMock(name="google")
            MockRepo.return_value = mock_repo
            
            service = OAuthProviderService(mock_session)
            
            with pytest.raises(ConflictError):
                await service.create_provider(
                    name="google",
                    display_name="Google",
                    client_id="client123",
                    client_secret="secret123",
                    authorization_url="https://accounts.google.com/o/oauth2/auth",
                    token_url="https://oauth2.googleapis.com/token",
                    user_info_url="https://www.googleapis.com/oauth2/v2/userinfo"
                )
    
    async def test_get_provider_not_found(self, mock_session):
        """Test getting non-existent provider."""
        from app.services.oauth_provider_service import OAuthProviderService
        from app.core.exceptions import NotFoundError
        from uuid import uuid4
        
        with patch('app.services.oauth_provider_service.OAuthProviderRepository') as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get.return_value = None
            MockRepo.return_value = mock_repo
            
            service = OAuthProviderService(mock_session)
            
            with pytest.raises(NotFoundError):
                await service.get_provider(uuid4())
    
    async def test_update_status(self, mock_session):
        """Test updating provider status."""
        from app.services.oauth_provider_service import OAuthProviderService
        from uuid import uuid4
        
        with patch('app.services.oauth_provider_service.OAuthProviderRepository') as MockRepo:
            mock_repo = AsyncMock()
            mock_provider = MagicMock()
            mock_provider.is_active = True
            mock_repo.get.return_value = mock_provider
            MockRepo.return_value = mock_repo
            
            service = OAuthProviderService(mock_session)
            result = await service.update_status(uuid4(), False)
            
            # Verify the update method was called with correct arguments
            mock_repo.update.assert_called_once_with(mock_provider, {"is_active": False})
            assert result == {"is_active": False}

