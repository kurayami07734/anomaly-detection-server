from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import CONFIG

engine = create_async_engine(CONFIG.POSTGRES_URL, echo=True, future=True)

AsyncSessionMaker = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get an async database session.
    Ensures the session is always closed after the request.
    """
    async with AsyncSessionMaker() as session:
        yield session
