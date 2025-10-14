from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import AsyncGenerator
import asyncio
import uuid
import random

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.models import Transaction
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
    async with AsyncSessionMaker() as session:
        yield session


async def main() -> None:
    print("Creating table if it doesn't exist...")

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    print("Table created.")

    user_ids = [uuid.uuid4() for _ in range(10)]
    transactions_to_create = []

    print("Generating transaction data...")

    for user_id in user_ids:
        start_date = datetime.now(tz=timezone.utc)
        for _ in range(15_000):
            amount = Decimal(random.uniform(10.0, 100000.0)).quantize(Decimal("0.01"))
            status = random.choice(["paid", "failed"])
            # Create transactions over a time span of ~1 year
            txn_date = start_date - timedelta(seconds=random.randint(0, 31_536_000))

            transactions_to_create.append(
                Transaction(
                    user_id=user_id,
                    amount=amount,
                    currency="INR",
                    txn_date=txn_date,
                    status=status,
                    meta_data=None,  # Explicitly set to None as requested
                )
            )

    print(f"Inserting {len(transactions_to_create)} transactions into the database...")
    async for session in get_session():
        async with session.begin():
            # Use bulk_save_objects for efficiency with many objects
            session.add_all(transactions_to_create)
        # The commit is handled by the async with session.begin() context manager

    print("Data loading complete.")


if __name__ == "__main__":
    # To run the async main function
    asyncio.run(main())
