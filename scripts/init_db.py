"""
Initialize database tables.
Run this script to create all database tables.

Usage:
    python -m scripts.init_db
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import init_db

async def main():
    print("Creating database tables...")
    await init_db()
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(main())
