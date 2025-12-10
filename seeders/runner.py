"""
Seeder runner - discovers and runs all seeders.
"""
import importlib
import pkgutil
from pathlib import Path
from typing import List, Type

from sqlmodel.ext.asyncio.session import AsyncSession
from seeders.base import BaseSeeder


def discover_seeders() -> List[Type[BaseSeeder]]:
    """Discover all seeder classes in the seeders directory."""
    seeders = []
    seeders_path = Path(__file__).parent
    
    for _, module_name, _ in pkgutil.iter_modules([str(seeders_path)]):
        # Skip non-seeder modules
        if module_name in ("base", "runner", "__init__") or module_name.startswith("_"):
            continue
        
        module = importlib.import_module(f"seeders.{module_name}")
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type) 
                and issubclass(attr, BaseSeeder) 
                and attr is not BaseSeeder
            ):
                seeders.append(attr)
    
    # Sort by order
    return sorted(seeders, key=lambda s: s.order)


async def run_all_seeders(session: AsyncSession, force: bool = False) -> None:
    """Run all discovered seeders."""
    seeders = discover_seeders()
    
    if not seeders:
        print("No seeders found.")
        return
    
    print(f"Found {len(seeders)} seeders.")
    
    for seeder_class in seeders:
        seeder = seeder_class(session)
        
        if force or await seeder.should_run():
            print(f"Running {seeder.name}...")
            await seeder.run()
        else:
            print(f"Skipping {seeder.name} (already seeded)")


async def run_seeder(session: AsyncSession, seeder_name: str, force: bool = False) -> None:
    """Run a specific seeder by name."""
    seeders = discover_seeders()
    
    for seeder_class in seeders:
        if seeder_class.__name__.lower() == seeder_name.lower() or \
           seeder_class.__name__.lower().replace("seeder", "") == seeder_name.lower():
            seeder = seeder_class(session)
            
            if force or await seeder.should_run():
                print(f"Running {seeder.name}...")
                await seeder.run()
            else:
                print(f"Skipping {seeder.name} (already seeded)")
            return
    
    print(f"Seeder '{seeder_name}' not found.")
    print("Available seeders:")
    for s in seeders:
        print(f"  - {s.__name__}")
