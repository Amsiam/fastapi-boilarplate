"""
Authentication service for user registration, login, and token management.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import uuid4
from fastapi import Request

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_token_hash
)
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError
)
from app.core.cache import delete_cache, user_permissions_key
from app.core.schemas.response import ErrorCode
from app.modules.users.models import User, Customer
from app.modules.auth.token_models import RefreshToken
from app.constants.enums import UserType
from app.modules.users.repository import UserRepository, CustomerRepository
from app.modules.auth.repository import RefreshTokenRepository
from app.modules.audit.service import audit_service


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db
        self.user_repo = UserRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.token_repo = RefreshTokenRepository(db)
    
    async def register_customer(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone_number: Optional[str] = None,
        request: Optional[Request] = None
    ) -> User:
        """
        Register a new customer user.
        
        Args:
            email: User email
            password: Plain password
            first_name: First name
            last_name: Last name
            phone_number: Optional phone number
            request: Optional request object for audit logging
            
        Returns:
            Created user
            
        Raises:
            ConflictError: If email already exists
        """
        # Check if user exists
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise ConflictError(
                error_code=ErrorCode.USER_ALREADY_EXISTS,
                message="User with this email already exists"
            )
        
        # Create user
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            user_type=UserType.CUSTOMER,
            is_active=True,
            is_verified=False  # Requires email verification
        )
        user = await self.user_repo.create(user)
        
        # Create customer profile
        customer = Customer(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number
        )
        await self.customer_repo.create(customer)
        
        # Audit Log
        await audit_service.log_action(
            action="register_customer",
            actor_id=user.id,
            target_id=str(user.id),
            target_type="user",
            details={
                "email": email,
                "first_name": first_name,
                "last_name": last_name
            },
            request=request
        )
        
        return user
    
    async def authenticate_user(
        self, 
        email: str, 
        password: str,
        request: Optional[Request] = None
    ) -> User:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: Plain password
            request: Optional request object for audit logging
            
        Returns:
            Authenticated user
            
        Raises:
            AuthenticationError: If credentials are invalid or user is inactive
        """
        user = await self.user_repo.get_by_email(email)
        
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError(
                error_code=ErrorCode.INVALID_CREDENTIALS,
                message="Invalid email or password"
            )
        
        if not user.is_active:
            raise AuthenticationError(
                error_code=ErrorCode.ACCOUNT_INACTIVE,
                message="Account is inactive"
            )
        
        # Audit Log (Login Success)
        await audit_service.log_action(
            action="user_login",
            actor_id=user.id,
            target_id=str(user.id),
            target_type="user",
            details={"email": email, "role": user.user_type.value},
            request=request
        )
        
        return user
    
    async def create_tokens(self, user: User) -> Tuple[str, str]:
        """
        Create access and refresh tokens for user.
        
        Args:
            user: User object
            
        Returns:
            Tuple of (access_token, refresh_token)
        """
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "user_type": user.user_type.value}
        )
        
        # Create refresh token
        refresh_token_value = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # Store refresh token in database
        family_id = uuid4()
        token_hash = generate_token_hash(refresh_token_value)
        
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            family_id=family_id,
            revoked=False
        )
        await self.token_repo.create(refresh_token)
        
        return access_token, refresh_token_value
    
    async def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        """
        Refresh access token using refresh token (with rotation).
        
        Args:
            refresh_token: Current refresh token
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
            
        Raises:
            AuthenticationError: If refresh token is invalid or revoked
        """
        # Decode token
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationError(
                error_code=ErrorCode.INVALID_REFRESH_TOKEN,
                message="Invalid refresh token"
            )
        
        # Get token from database
        token_hash = generate_token_hash(refresh_token)
        db_token = await self.token_repo.get_by_token_hash(token_hash)
        
        if not db_token:
            raise AuthenticationError(
                error_code=ErrorCode.INVALID_REFRESH_TOKEN,
                message="Refresh token not found"
            )
        
        # Check if revoked (reuse detection)
        if db_token.revoked:
            # Revoke entire token family
            await self.token_repo.revoke_family(db_token.family_id)
            raise AuthenticationError(
                error_code=ErrorCode.INVALID_REFRESH_TOKEN,
                message="Refresh token has been revoked"
            )
        
        # Check expiration
        if db_token.expires_at < datetime.utcnow():
            raise AuthenticationError(
                error_code=ErrorCode.TOKEN_EXPIRED,
                message="Refresh token has expired"
            )
        
        # Revoke current token
        await self.token_repo.revoke_token(db_token.id)
        
        # Get user
        user = await self.user_repo.get(db_token.user_id)
        if not user:
            raise NotFoundError(
                error_code=ErrorCode.USER_NOT_FOUND,
                message="User not found"
            )
        
        # Create new tokens
        return await self.create_tokens(user)
    
    async def verify_email(self, user_id: str) -> None:
        """
        Mark user email as verified.
        
        Args:
            user_id: User ID
        """
        user = await self.user_repo.get(user_id)
        if user:
            await self.user_repo.update(user, {"is_verified": True})
    
    async def logout(self, user_id: str, request: Optional[Request] = None) -> None:
        """
        Logout user by revoking all refresh tokens.
        
        Args:
            user_id: User ID
            request: Optional request object for audit logging
        """
        # Revoke all user tokens
        tokens = await self.token_repo.get_by_user_id(user_id)
        for token in tokens:
            await self.token_repo.revoke_token(token.id)
        
        # Clear permission cache
        cache_key = user_permissions_key(str(user_id))
        await delete_cache(cache_key)
        
        # Audit Log
        await audit_service.log_action(
            action="user_logout",
            actor_id=user_id,
            target_id=str(user_id),
            target_type="user",
            request=request
        )
    
    async def reset_password(self, email: str, new_password: str) -> None:
        """
        Reset user password.
        
        Args:
            email: User email
            new_password: New password
            
        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise NotFoundError(
                error_code=ErrorCode.USER_NOT_FOUND,
                message="User not found"
            )
        
        # Update password
        await self.user_repo.update(user, {
            "hashed_password": get_password_hash(new_password)
        })
        
        # Revoke all refresh tokens (force re-login)
        await self.logout(str(user.id))

