"""
User repository for database operations.
"""
from typing import Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.users.models import User, Admin, Customer
from app.core.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await self.get_by_field("email", email)
    
    async def get_admin_by_user_id(self, user_id: UUID) -> Optional[Admin]:
        """Get admin record by user ID."""
        result = await self.db.execute(
            select(Admin).where(Admin.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_customer_by_user_id(self, user_id: UUID) -> Optional[Customer]:
        """Get customer record by user ID."""
        result = await self.db.execute(
            select(Customer).where(Customer.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def soft_delete(self, user_id: UUID) -> bool:
        """
        Soft delete user by setting is_active=False and renaming email.
        This allows the email to be re-registered.
        """
        from datetime import datetime
        
        user = await self.get(user_id)
        if not user:
            return False
        
        # Rename email to allow reuse: deleted_{timestamp}_{email}
        # Truncate if too long (email max 255)
        timestamp = int(datetime.utcnow().timestamp())
        prefix = f"deleted_{timestamp}_"
        original_email = user.email
        
        # Ensure we don't exceed max length
        max_email_len = 255
        if len(prefix) + len(original_email) > max_email_len:
            # Keep unique part
            available_len = max_email_len - len(prefix)
            original_email = original_email[:available_len]
            
        new_email = f"{prefix}{original_email}"
        
        user.is_active = False
        user.email = new_email
        user.deleted_at = datetime.utcnow()
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return True


class AdminRepository(BaseRepository[Admin]):
    """Repository for Admin model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Admin, db)
    
    async def get_by_username(self, username: str) -> Optional[Admin]:
        """Get admin by username."""
        return await self.get_by_field("username", username)
    
    async def get_by_user_id(self, user_id: UUID) -> Optional[Admin]:
        """Get admin by user ID."""
        return await self.get_by_field("user_id", user_id)


class CustomerRepository(BaseRepository[Customer]):
    """Repository for Customer model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Customer, db)
    
    async def get_by_user_id(self, user_id: UUID) -> Optional[Customer]:
        """Get customer by user ID."""
        return await self.get_by_field("user_id", user_id)
