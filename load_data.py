from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import AsyncGenerator
import asyncio
from collections import deque
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
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    print("Table created.")

    user_ids = [uuid.uuid4() for _ in range(10)]
    transactions_to_create = []

    print("Generating transaction data...")

    ROLLING_WINDOW_SIZE = 20
    MIN_TXNS_FOR_ANOMALY_CHECK = 10
    ANOMALY_CHANCE = 0.35

    for user_id in user_ids:
        # Maintain a deque for the rolling window of recent transaction amounts for each user
        recent_amounts = deque(maxlen=ROLLING_WINDOW_SIZE)
        start_date = datetime.now(tz=timezone.utc)

        for _ in range(15_000):
            # Introduce occasional large spikes to generate more anomalies
            if random.random() < ANOMALY_CHANCE:
                # Potential anomaly: generate a large amount
                amount = Decimal(random.uniform(5_000.0, 100_000.0)).quantize(
                    Decimal("0.01")
                )
            else:
                # Normal transaction: generate a small amount to keep the rolling mean low
                amount = Decimal(random.uniform(10.0, 500.0)).quantize(Decimal("0.01"))

            status = random.choice(["paid", "failed"])

            # Create transactions over a time span of ~1 year
            txn_date = start_date - timedelta(seconds=random.randint(0, 31_536_000))

            is_anomaly = False
            # Check for anomaly only if we have enough historical data
            if len(recent_amounts) >= MIN_TXNS_FOR_ANOMALY_CHECK:
                rolling_mean = sum(recent_amounts) / len(recent_amounts)
                if amount > (5 * rolling_mean):
                    is_anomaly = True

            # Add the current amount to our rolling window
            recent_amounts.append(amount)

            transactions_to_create.append(
                Transaction(
                    user_id=user_id,
                    amount=amount,
                    currency="INR",
                    txn_date=txn_date,
                    status=status,
                    meta_data={"is_anomaly": is_anomaly},
                )
            )

    print(f"Inserting {len(transactions_to_create)} transactions into the database...")

    async for session in get_session():
        async with session.begin():
            session.add_all(transactions_to_create)

    print("Data loading complete.")


if __name__ == "__main__":
    # To run the async main function
    asyncio.run(main())
