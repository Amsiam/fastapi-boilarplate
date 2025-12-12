"""
OAuth Provider service for managing OAuth providers.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import Request

from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.auth.repository import OAuthProviderRepository
from app.modules.oauth.models import OAuthProvider
from app.core.exceptions import NotFoundError, ConflictError
from app.constants.error_codes import ErrorCode
from app.modules.audit.service import audit_service


class OAuthProviderService:
    """Service for OAuth provider management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider_repo = OAuthProviderRepository(db)
    
    async def create_provider(
        self,
        name: str,
        display_name: str,
        client_id: str,
        client_secret: str,
        authorization_url: str,
        token_url: str,
        user_info_url: str,
        actor_id: UUID,
        scopes: List[str] = None,
        icon: Optional[str] = None,
        is_active: bool = True,
        request: Optional[Request] = None
    ) -> dict:
        """
        Create a new OAuth provider.
        """
        # Check if provider with same name exists
        existing = await self.provider_repo.get_by_name(name.lower())
        if existing:
            raise ConflictError(
                error_code=ErrorCode.DUPLICATE_ENTRY,
                message=f"OAuth provider with name '{name}' already exists"
            )
        
        # Create provider
        provider = OAuthProvider(
            name=name.lower(),
            display_name=display_name,
            client_id=client_id,
            client_secret=client_secret,
            authorization_url=authorization_url,
            token_url=token_url,
            user_info_url=user_info_url,
            scopes=scopes or [],
            icon=icon,
            is_active=is_active
        )
        
        created_provider = await self.provider_repo.create(provider)
        
        await audit_service.log_action(
            action="create_oauth_provider",
            actor_id=actor_id,
            target_id=str(created_provider.id),
            target_type="oauth_provider",
            details={"name": created_provider.name, "display_name": created_provider.display_name},
            request=request
        )
        
        return {
            "id": str(created_provider.id),
            "name": created_provider.name,
            "display_name": created_provider.display_name,
            "icon": created_provider.icon,
            "is_active": created_provider.is_active,
            "created_at": created_provider.created_at
        }
    
    async def list_providers(
        self, 
        include_inactive: bool = True,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """
        List all OAuth providers with pagination.
        """
        skip = (page - 1) * per_page
        
        # Use repository method
        providers, total = await self.provider_repo.list_paginated(
            skip=skip,
            limit=per_page,
            include_inactive=include_inactive
        )
        
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        
        return {
            "items": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "display_name": p.display_name,
                    "icon": p.icon,
                    "is_active": p.is_active,
                    "created_at": p.created_at.isoformat()
                }
                for p in providers
            ],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    
    async def get_provider(self, provider_id: UUID) -> dict:
        """
        Get OAuth provider details.
        """
        provider = await self.provider_repo.get(provider_id)
        
        if not provider:
            raise NotFoundError(
                error_code=ErrorCode.OAUTH_PROVIDER_NOT_FOUND,
                message="OAuth provider not found"
            )
        
        return {
            "id": str(provider.id),
            "name": provider.name,
            "display_name": provider.display_name,
            "icon": provider.icon,
            "client_id": provider.client_id,
            "authorization_url": provider.authorization_url,
            "token_url": provider.token_url,
            "user_info_url": provider.user_info_url,
            "scopes": provider.scopes,
            "is_active": provider.is_active,
            "created_at": provider.created_at.isoformat(),
            "updated_at": provider.updated_at.isoformat()
        }
    
    async def update_provider(self, provider_id: UUID, actor_id: UUID, request: Optional[Request] = None, **update_data) -> None:
        """
        Update OAuth provider configuration.
        """
        provider = await self.provider_repo.get(provider_id)
        
        if not provider:
            raise NotFoundError(
                error_code=ErrorCode.OAUTH_PROVIDER_NOT_FOUND,
                message="OAuth provider not found"
            )
        
        old_values = {k: getattr(provider, k) for k in update_data.keys() if hasattr(provider, k)}
        
        # Update fields
        for field, value in update_data.items():
            if value is not None:
                setattr(provider, field, value)
        
        provider.updated_at = datetime.utcnow()
        await self.provider_repo.update(provider, update_data)
        
        await audit_service.log_action(
            action="update_oauth_provider",
            actor_id=actor_id,
            target_id=str(provider.id),
            target_type="oauth_provider",
            old_values=old_values,
            new_values=update_data,
            request=request
        )
    
    async def update_status(self, provider_id: UUID, is_active: bool, actor_id: UUID, request: Optional[Request] = None) -> dict:
        """
        Activate or deactivate an OAuth provider.
        """
        provider = await self.provider_repo.get(provider_id)
        
        if not provider:
            raise NotFoundError(
                error_code=ErrorCode.OAUTH_PROVIDER_NOT_FOUND,
                message="OAuth provider not found"
            )
        
        old_status = provider.is_active
        await self.provider_repo.update(provider, {"is_active": is_active})
        
        await audit_service.log_action(
            action="update_oauth_provider_status",
            actor_id=actor_id,
            target_id=str(provider.id),
            target_type="oauth_provider",
            old_values={"is_active": old_status},
            new_values={"is_active": is_active},
            request=request
        )
        
        return {"is_active": is_active}
    
    async def delete_provider(self, provider_id: UUID, actor_id: UUID, request: Optional[Request] = None) -> None:
        """
        Delete an OAuth provider.
        """
        provider = await self.provider_repo.get(provider_id)
        
        if not provider:
            raise NotFoundError(
                error_code=ErrorCode.OAUTH_PROVIDER_NOT_FOUND,
                message="OAuth provider not found"
            )
        
        # Check if provider has linked accounts using repository
        if await self.provider_repo.has_linked_accounts(provider_id):
            raise ConflictError(
                error_code=ErrorCode.OAUTH_PROVIDER_HAS_ACCOUNTS,
                message="Cannot delete provider with linked user accounts"
            )
        
        await self.provider_repo.delete(provider_id)
        
        await audit_service.log_action(
            action="delete_oauth_provider",
            actor_id=actor_id,
            target_id=str(provider.id),
            target_type="oauth_provider",
            details={"name": provider.name},
            request=request
        )
