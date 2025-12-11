"""
OAuth2 service for handling social authentication.
"""
import httpx
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from uuid import uuid4

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.modules.users.models import User, Customer
from app.modules.oauth.models import OAuthProvider, OAuthAccount
from app.modules.auth.repository import OAuthProviderRepository, OAuthAccountRepository
from app.modules.users.repository import UserRepository, CustomerRepository
from app.constants.enums import UserType
from app.core.schemas.response import ErrorCode
from app.core.exceptions import AuthenticationError, NotFoundError, ConflictError


class OAuthService:
    """Service for OAuth2 authentication."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider_repo = OAuthProviderRepository(db)
        self.account_repo = OAuthAccountRepository(db)
        self.user_repo = UserRepository(db)
        self.customer_repo = CustomerRepository(db)
    
    async def list_providers(self) -> list[dict]:
        """List all active OAuth providers."""
        providers = await self.provider_repo.get_active_providers()
        return [
            {
                "name": p.name,
                "display_name": p.display_name,
                "icon": p.icon,
                "login_url": f"{settings.API_V1_STR}/auth/oauth/login/{p.name}"
            }
            for p in providers
        ]
    
    async def get_login_url(self, provider_name: str, redirect_uri: str) -> str:
        """
        Generate authorization URL for a provider.
        
        Args:
            provider_name: Name of the provider (e.g., "google")
            redirect_uri: Callback URL where provider will redirect
            
        Returns:
            Authorization URL
        """
        provider = await self.provider_repo.get_by_name(provider_name)
        if not provider:
            raise NotFoundError(
                error_code=ErrorCode.OAUTH_PROVIDER_NOT_FOUND,
                message=f"Provider '{provider_name}' not found"
            )
        
        params = {
            "client_id": provider.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(provider.scopes) if isinstance(provider.scopes, list) else provider.scopes,
            "state": str(uuid4()),  # Random state for CSRF protection
            "access_type": "offline",  # Request refresh token (Google specific)
            "prompt": "consent"  # Force consent screen (Google specific)
        }
        
        return f"{provider.authorization_url}?{urlencode(params)}"
    
    async def handle_callback(
        self, 
        provider_name: str, 
        code: str, 
        redirect_uri: str
    ) -> dict:
        """
        Handle OAuth callback code exchange.
        
        Args:
            provider_name: Name of the provider
            code: Authorization code
            redirect_uri: Callback URL used in original request
            
        Returns:
            Dictionary with access_token and refresh_token
        """
        provider = await self.provider_repo.get_by_name(provider_name)
        if not provider:
            raise NotFoundError(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message=f"Provider '{provider_name}' not found"
            )
            
        # 1. Exchange code for access token
        token_data = await self._exchange_code(provider, code, redirect_uri)
        
        # 2. Get user info from provider
        user_info = await self._get_user_info(provider, token_data["access_token"])
        
        # 3. Find or create user
        user = await self._get_or_create_user(provider, user_info)
        
        # 4. Generate JWT tokens
        access_token = create_access_token(subject=str(user.id), role=user.role)
        refresh_token = await create_refresh_token(user.id, self.db)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    async def _exchange_code(self, provider: OAuthProvider, code: str, redirect_uri: str) -> dict:
        """Exchange authorization code for access token."""
        data = {
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        headers = {"Accept": "application/json"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(provider.token_url, data=data, headers=headers)
            
            if response.status_code != 200:
                raise AuthenticationError(
                    error_code=ErrorCode.OAUTH_ERROR,
                    message=f"Failed to retrieve access token from {provider.name}"
                )
                
            return response.json()
            
    async def _get_user_info(self, provider: OAuthProvider, access_token: str) -> dict:
        """Fetch user profile from provider."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(provider.user_info_url, headers=headers)
            
            if response.status_code != 200:
                raise AuthenticationError(
                    error_code=ErrorCode.OAUTH_ERROR,
                    message=f"Failed to retrieve user info from {provider.name}"
                )
                
            return response.json()
    
    async def _get_or_create_user(self, provider: OAuthProvider, user_info: dict) -> User:
        """Find existing user or create new one."""
        # Extract email and provider user ID
        # Note: Different providers have different response structures
        email = user_info.get("email")
        provider_user_id = str(user_info.get("id") or user_info.get("sub"))
        
        if not email:
            raise AuthenticationError(
                error_code=ErrorCode.OAUTH_ERROR,
                message="Email not provided by OAuth provider"
            )
            
        # Check if OAuth account exists
        oauth_account = await self.account_repo.get_by_provider_user_id(
            provider.id, 
            provider_user_id
        )
        
        if oauth_account:
            # Return associated user
            return await self.user_repo.get(oauth_account.user_id)
            
        # Check if user with email exists
        user = await self.user_repo.get_by_email(email)
        
        if user:
            # Link existing user to OAuth provider
            await self._link_account(user, provider, provider_user_id, email)
            return user
            
        # Create new user (Customer)
        user = await self._create_oauth_user(email)
        await self._link_account(user, provider, provider_user_id, email)
        
        return user
        
    async def _create_oauth_user(self, email: str) -> User:
        """Create a new user from OAuth data."""
        # Create User
        user = User(
            email=email,
            hashed_password="",  # No password for OAuth users
            is_active=True,
            is_verified=True,  # Trusted provider
            user_type=UserType.CUSTOMER
        )
        self.db.add(user)
        await self.db.flush()
        
        # Create Customer profile
        customer = Customer(user_id=user.id)
        self.db.add(customer)
        
        return user
        
    async def _link_account(
        self, 
        user: User, 
        provider: OAuthProvider, 
        provider_user_id: str, 
        email: str
    ):
        """Link a user to an OAuth provider."""
        account = OAuthAccount(
            user_id=user.id,
            provider_id=provider.id,
            provider_user_id=provider_user_id,
            email=email
        )
        self.db.add(account)
        await self.db.commit()
