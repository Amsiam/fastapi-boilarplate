import os
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlalchemy import text

from app.main import app
from app.core.config import settings
from app.core.database import get_db

# Database configuration
DB_HOST = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
TEST_DB_NAME = "test_db"

# URL for connecting to the default 'postgres' database to create/drop the test db
DEFAULT_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:5432/postgres"
# URL for the test database
TEST_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:5432/{TEST_DB_NAME}"

@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create test database before tests and drop it after."""
    # Connect to default database to create test_db
    default_engine = create_async_engine(DEFAULT_DATABASE_URL, isolation_level="AUTOCOMMIT")
    
    async with default_engine.connect() as conn:
        # Check if database exists
        result = await conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB_NAME}'"))
        if not result.scalar():
            await conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    
    await default_engine.dispose()
    
    yield
    
    # Drop test database after tests
    # Re-connect to default database
    default_engine = create_async_engine(DEFAULT_DATABASE_URL, isolation_level="AUTOCOMMIT")
    async with default_engine.connect() as conn:
        # Terminate connections to test_db before dropping
        await conn.execute(text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
            AND pid <> pg_backend_pid()
        """))
        await conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
    
    await default_engine.dispose()

engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def init_db(setup_test_db):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest.fixture
async def session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

from httpx import AsyncClient, ASGITransport

@pytest.fixture
async def client(session: AsyncSession) -> AsyncClient:
    def override_get_session():
        yield session
    
    app.dependency_overrides[get_db] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
