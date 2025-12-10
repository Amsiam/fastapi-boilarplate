"""
User repository for database operations.
"""
from typing import Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User, Admin, Customer
from app.repositories.base import BaseRepository


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
