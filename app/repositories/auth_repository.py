"""
Authentication repository for tokens and OAuth.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.auth import RefreshToken
from app.models.oauth import OAuthProvider, OAuthAccount
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository for RefreshToken model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(RefreshToken, db)
    
    async def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by hash."""
        return await self.get_by_field("token_hash", token_hash)
    
    async def get_by_user_id(self, user_id: UUID) -> List[RefreshToken]:
        """Get all refresh tokens for a user."""
        result = await self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked == False)
            .where(RefreshToken.expires_at > datetime.utcnow())
        )
        return result.scalars().all()
    
    async def revoke_token(self, token_id: UUID) -> bool:
        """Revoke a refresh token."""
        token = await self.get(token_id)
        if token:
            token.revoked = True
            await self.db.commit()
            return True
        return False
    
    async def revoke_family(self, family_id: UUID) -> int:
        """Revoke all tokens in a family."""
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.family_id == family_id)
        )
        tokens = result.scalars().all()
        
        count = 0
        for token in tokens:
            token.revoked = True
            count += 1
        
        await self.db.commit()
        return count


class OAuthProviderRepository(BaseRepository[OAuthProvider]):
    """Repository for OAuthProvider model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(OAuthProvider, db)
    
    async def get_by_name(self, name: str) -> Optional[OAuthProvider]:
        """Get OAuth provider by name."""
        return await self.get_by_field("name", name)
    
    async def get_active_providers(self) -> List[OAuthProvider]:
        """Get all active OAuth providers."""
        result = await self.db.execute(
            select(OAuthProvider).where(OAuthProvider.is_active == True)
        )
        return result.scalars().all()


class OAuthAccountRepository(BaseRepository[OAuthAccount]):
    """Repository for OAuthAccount model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(OAuthAccount, db)
    
    async def get_by_provider_user_id(
        self,
        provider_id: UUID,
        provider_user_id: str
    ) -> Optional[OAuthAccount]:
        """Get OAuth account by provider and provider user ID."""
        result = await self.db.execute(
            select(OAuthAccount)
            .where(OAuthAccount.provider_id == provider_id)
            .where(OAuthAccount.provider_user_id == provider_user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: UUID) -> List[OAuthAccount]:
        """Get all OAuth accounts for a user."""
        result = await self.db.execute(
            select(OAuthAccount).where(OAuthAccount.user_id == user_id)
        )
        return result.scalars().all()
