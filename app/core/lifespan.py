"""
Database initialization on startup.
This will create tables if they don't exist.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI.
    Runs on startup and shutdown.
    """
    # Startup: Create database tables
    print("🔄 Initializing database...")
    await init_db()
    print("✅ Database initialized successfully!")
    
    yield
    
    # Shutdown: cleanup if needed
    print("👋 Shutting down...")
