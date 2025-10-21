import asyncio
import os
import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio

# Set dummy environment variables before importing the app
# This is to prevent Pydantic from raising a ValidationError
# when the tests are being collected.
os.environ["POSTGRES_URL"] = "postgresql+asyncpg://test:test@localhost/test"
os.environ["REDIS_URL"] = "redis://localhost"

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from src.database import get_session
from src.main import app
from src.models import Transaction

# Use the aiosqlite driver for async support with an in-memory SQLite DB
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

USERS = [uuid.uuid4() for _ in range(10)]

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for debugging
    future=True,
    connect_args={"check_same_thread": False},
)

TestSessionMaker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="session")
def event_loop(request) -> Generator:
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture to create and teardown the test database for each test function.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with TestSessionMaker() as session:
        # Seed initial test data
        txns = [
            Transaction(
                user_id=user_id,
                amount=100.00,
                currency="INR",
                txn_date=(datetime.now(tz=UTC) - timedelta(days=365)),
                status="paid",
            )
            for user_id in USERS
        ]
        session.add_all(txns)
        await session.commit()

        yield session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture to create an AsyncClient with the database session dependency overridden.
    """

    async def get_session_override() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
