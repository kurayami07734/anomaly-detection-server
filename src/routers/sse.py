import asyncio
import random
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import AsyncGenerator, List, Tuple

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import AsyncSessionMaker
from src.models import Transaction
from src.redis import get_redis

router = APIRouter()


# Simulation constants
INTERVAL_SECONDS = 2
ROLLING_WINDOW_SIZE = 20
MIN_TXNS_FOR_ANOMALY_CHECK = 10
ANOMALY_CHANCE = 0.35
ANOMALY_MULTIPLIER = 5


async def _get_rolling_mean(
    redis_client: Redis, user_id: uuid.UUID
) -> Tuple[Decimal, List[Decimal]]:
    """Fetches recent transaction amounts and calculates the rolling mean."""
    redis_key = f"user:{user_id}:txn_amounts"
    recent_amounts_str = await redis_client.lrange(redis_key, 0, -1)
    recent_amounts = [Decimal(a) for a in recent_amounts_str]

    if not recent_amounts:
        return Decimal(0), []

    rolling_mean = sum(recent_amounts) / len(recent_amounts)
    return rolling_mean, recent_amounts


def _simulate_transaction_amount(
    rolling_mean: Decimal, is_potential_anomaly: bool
) -> Decimal:
    """Simulates a new transaction amount, potentially as an anomaly."""
    if is_potential_anomaly:
        # Generate a significantly larger amount than the mean or a high random value
        base_amount = max(float(rolling_mean) * ANOMALY_MULTIPLIER, 5000.0)
        amount = Decimal(random.uniform(base_amount, base_amount * 2))
    else:
        # Generate a "normal" transaction amount
        amount = Decimal(random.uniform(10.0, 500.0))

    return amount.quantize(Decimal("0.01"))


def _is_anomaly(amount: Decimal, rolling_mean: Decimal, num_recent_txns: int) -> bool:
    """Checks if a transaction is an anomaly based on the rolling mean."""
    return (
        num_recent_txns >= MIN_TXNS_FOR_ANOMALY_CHECK
        and rolling_mean > 0
        and amount > (ANOMALY_MULTIPLIER * rolling_mean)
    )


async def _create_and_persist_transaction(
    db: AsyncSession, user_id: uuid.UUID, amount: Decimal, is_anomaly: bool
) -> Transaction:
    """Creates a new Transaction object and saves it to the database."""
    new_txn = Transaction(
        user_id=user_id,
        amount=amount,
        currency="INR",
        txn_date=datetime.now(tz=timezone.utc),
        status=random.choice(["paid", "failed"]),
        meta_data={"is_anomaly": is_anomaly},
    )
    db.add(new_txn)
    await db.commit()
    await db.refresh(new_txn)
    return new_txn


async def _update_rolling_window(
    redis_client: Redis, user_id: uuid.UUID, amount: Decimal
):
    """Pushes the new transaction amount to Redis and trims the list."""
    redis_key = f"user:{user_id}:txn_amounts"
    await redis_client.lpush(redis_key, str(amount))
    await redis_client.ltrim(redis_key, 0, ROLLING_WINDOW_SIZE - 1)


async def event_generator(
    request: Request, user_id: uuid.UUID, redis_client: Redis
) -> AsyncGenerator[str, None]:
    """
    Generates and yields server-sent events for new transactions.

    This function orchestrates the simulation of transaction creation, checks for
    anomalies, and streams the results to the client. The process stops when the
    client disconnects.
    """
    try:
        print(f"Starting SSE connection for user {user_id}")
        yield ": ping\n\n"

        while True:
            # Check for client disconnection
            if await request.is_disconnected():
                print(f"Client for user {user_id} disconnected. Stopping simulation.")
                break

            # Create new DB session for each transaction to avoid timeout issues
            async with AsyncSessionMaker() as db:
                try:
                    # 1. Get historical data for anomaly check
                    print(redis_client)
                    rolling_mean, recent_amounts = await _get_rolling_mean(
                        redis_client, user_id
                    )

                    # 2. Simulate a new transaction amount
                    is_potential_anomaly = random.random() < ANOMALY_CHANCE
                    amount = _simulate_transaction_amount(
                        rolling_mean, is_potential_anomaly
                    )

                    # 3. Check if it's an anomaly
                    is_anomaly = _is_anomaly(amount, rolling_mean, len(recent_amounts))

                    # 4. Create and save the transaction
                    new_txn = await _create_and_persist_transaction(
                        db, user_id, amount, is_anomaly
                    )

                    # 5. Update the rolling window for the next iteration
                    await _update_rolling_window(redis_client, user_id, new_txn.amount)

                    # 6. Stream the event to the client
                    payload = new_txn.model_dump_json()
                    yield f"data: {payload}\n\n"

                except Exception as e:
                    print(f"Error processing transaction for user {user_id}: {e}")
                    # Send error event to client
                    yield f"event: error\ndata: {str(e)}\n\n"

            # Wait before next iteration
            await asyncio.sleep(INTERVAL_SECONDS)

    except asyncio.CancelledError:
        print(f"SSE connection cancelled for user {user_id}")
        raise
    except Exception as e:
        print(f"Fatal error in SSE event generator for user {user_id}: {e}")
        yield f"event: error\ndata: Fatal error: {str(e)}\n\n"
    finally:
        print(f"Closing SSE connection for user {user_id}")


@router.get("/sse/transactions/{user_id}")
async def sse_transactions(
    request: Request, user_id: uuid.UUID, redis_client: Redis = Depends(get_redis)
):
    """
    Establishes an SSE connection to stream simulated transactions for a user.
    """
    print("SSE connection established")
    return StreamingResponse(
        event_generator(request, user_id, redis_client),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
