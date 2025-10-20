import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.database import get_session
from src.main import app
from src.models import Transaction

# Use the aiosqlite driver for async support with an in-memory SQLite DB
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

USERS = [uuid.uuid4() for _ in range(10)]

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

TestSessionMaker = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop(request) -> Generator:
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture to create and teardown the test database for each test function.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with TestSessionMaker() as session:
        async with session.begin():
            txns = [
                Transaction(
                    user_id=user_id,
                    amount=100.00,
                    currency="INR",
                    txn_date=datetime.now(tz=timezone.utc),
                    status="paid",
                )
                for user_id in USERS
            ]
            session.add_all(txns)

        yield session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[TestClient, None]:
    """
    Fixture to create a TestClient with the database session dependency overridden.
    """

    async def get_session_override() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()
