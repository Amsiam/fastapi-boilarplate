"""
Base seeder class that all seeders should inherit from.
"""
from abc import ABC, abstractmethod
from sqlmodel.ext.asyncio.session import AsyncSession


class BaseSeeder(ABC):
    """Base class for database seeders."""
    
    # Order in which seeders should run (lower runs first)
    order: int = 100
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @abstractmethod
    async def run(self) -> None:
        """Run the seeder to populate data."""
        pass
    
    @abstractmethod
    async def should_run(self) -> bool:
        """Check if this seeder should run (e.g., data doesn't already exist)."""
        pass
    
    @property
    def name(self) -> str:
        """Return the seeder name."""
        return self.__class__.__name__
