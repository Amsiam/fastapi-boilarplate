"""
FastAPI lifespan event handler.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    print("🚀 Application starting up...")
    
    # MongoDB connection
    from app.core.mongo import mongodb
    mongodb.connect()
    
    # NOTE: Database tables are managed by Alembic migrations
    # Run: alembic upgrade head
    # For development auto-creation, uncomment below:
    # from app.core.database import init_db
    # await init_db()
    
    yield
    
    # Mongo Shutdown
    mongodb.close()
    
    # Shutdown
    print("👋 Application shutting down...")
