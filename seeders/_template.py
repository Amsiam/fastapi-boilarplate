# This is a template file - not meant to be imported directly.
# Copy and modify this file when creating new seeders.

"""
{name} Seeder
"""
from sqlmodel import select
from seeders.base import BaseSeeder


class ExampleSeeder(BaseSeeder):
    """Example seeder - copy this file to create new seeders."""
    
    order = 100  # Adjust order as needed (lower runs first)
    
    async def should_run(self) -> bool:
        """Check if this seeder should run."""
        # TODO: Implement check - return True if data needs to be seeded
        # Example: Check if a table is empty
        return True
    
    async def run(self) -> None:
        """Run the seeder."""
        # TODO: Implement seeding logic
        # Example:
        # item = MyModel(name="test")
        # self.session.add(item)
        # await self.session.commit()
        pass
