import os

# Set test mode flag to disable rate limiting
os.environ["TESTING"] = "1"

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlalchemy import text
from sqlalchemy.pool import NullPool

from app.main import app as main_app
from app.core.database import get_db
from app.core.cache import reset_redis_client

# Database configuration
DB_HOST = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
TEST_DB_NAME = "test_db"

# URL for connecting to the default 'postgres' database to create/drop the test db
DEFAULT_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:5432/postgres"
# URL for the test database
TEST_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:5432/{TEST_DB_NAME}"

# Create test engine with NullPool to avoid connection reuse issues
test_engine = create_async_engine(
    TEST_DATABASE_URL, 
    echo=False, 
    future=True,
    poolclass=NullPool  # Disable connection pooling to avoid conflicts
)
TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create test database before tests and drop it after."""
    default_engine = create_async_engine(DEFAULT_DATABASE_URL, isolation_level="AUTOCOMMIT")
    
    try:
        async with default_engine.connect() as conn:
            result = await conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB_NAME}'"))
            if not result.scalar():
                await conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    except Exception:
        raise
    
    await default_engine.dispose()
    
    yield
    
    # Drop test database after tests
    default_engine = create_async_engine(DEFAULT_DATABASE_URL, isolation_level="AUTOCOMMIT")
    async with default_engine.connect() as conn:
        await conn.execute(text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
            AND pid <> pg_backend_pid()
        """))
        await conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
    
    await default_engine.dispose()



@pytest.fixture(scope="session", autouse=True)
async def init_db(setup_test_db):
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest.fixture
async def session() -> AsyncSession:
    """Provide a database session for direct test use."""
    async with TestSessionLocal() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()

@pytest.fixture
async def client(session: AsyncSession) -> AsyncClient:
    """
    Create test client that shares the test session.
    This ensures data seeded in tests is visible to API endpoints.
    """
    
    async def override_get_db():
        """Override dependency to use the test session."""
        yield session
    
    main_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=main_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    main_app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_redis():
    """Reset Redis client before each test to avoid event loop conflicts."""
    reset_redis_client()
    yield
    reset_redis_client()

@pytest.fixture(autouse=True)
def setup_mongo_test_db():
    """Configure MongoDB to use a test database."""
    from app.core.mongo import mongodb
    
    # Store original and set test database name
    original_db_name = mongodb.db_name
    mongodb.db_name = "test_audit_logs"
    
    # Force fresh connection
    mongodb.close()
    
    yield
    
    # Restore original and close
    mongodb.db_name = original_db_name
    mongodb.close()

@pytest.fixture(autouse=True)
async def clean_mongo(setup_mongo_test_db):
    """Clean MongoDB test database before and after each test."""
    from app.core.mongo import mongodb
    
    # Ensure connected
    if mongodb.client is None:
        try:
            mongodb.connect()
        except Exception:
            pass
            
    db = mongodb.get_db()
    
    # Safe cleanup that ignores connection errors
    if db is not None and db.name == "test_audit_logs":
        try:
            await db["audit_logs"].delete_many({})
        except Exception:
            pass
        
    yield
    
    # Cleanup after test
    try:
        if mongodb.client is not None:
            db = mongodb.get_db()
            if db is not None and db.name == "test_audit_logs":
                await db["audit_logs"].delete_many({})
    except Exception:
        pass
