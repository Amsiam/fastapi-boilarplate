"""
Base repository class for database operations.
"""
from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Initialize repository.
        
        Args:
            model: SQLModel class
            db: Database session
        """
        self.model = model
        self.db = db
    
    async def get(self, id: UUID) -> Optional[ModelType]:
        """
        Get a record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Model instance or None
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_field(self, field_name: str, value: any) -> Optional[ModelType]:
        """
        Get a record by field value.
        
        Args:
            field_name: Field name
            value: Field value
            
        Returns:
            Model instance or None
        """
        field = getattr(self.model, field_name)
        result = await self.db.execute(
            select(self.model).where(field == value)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of model instances
        """
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, obj_in: ModelType) -> ModelType:
        """
        Create a new record.
        
        Args:
            obj_in: Model instance to create
            
        Returns:
            Created model instance
        """
        self.db.add(obj_in)
        await self.db.commit()
        await self.db.refresh(obj_in)
        return obj_in
    
    async def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        """
        Update a record.
        
        Args:
            db_obj: Existing model instance
            obj_in: Dictionary of fields to update
            
        Returns:
            Updated model instance
        """
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: UUID) -> bool:
        """
        Delete a record.
        
        Args:
            id: Record ID
            
        Returns:
            True if deleted, False if not found
        """
        obj = await self.get(id)
        if obj:
            await self.db.delete(obj)
            await self.db.commit()
            return True
        return False
