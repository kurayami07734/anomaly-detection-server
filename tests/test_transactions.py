from datetime import UTC, datetime, timedelta
from decimal import Decimal
from urllib.parse import urlencode

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Transaction
from tests.conftest import USERS


@pytest.fixture(scope="module")
def fixed_utc_now() -> datetime:
    """Return a fixed, timezone-aware datetime object for deterministic tests."""
    return datetime.now(tz=UTC)


@pytest_asyncio.fixture(scope="function")
async def seed_transactions(db_session: AsyncSession, fixed_utc_now: datetime):
    """
    Seeds the database with a more diverse set of transactions for a single user
    to allow for better testing of filtering and pagination.
    """
    user_id = USERS[0]
    base_date = fixed_utc_now
    txns = []
    for i in range(20):
        txns.append(
            Transaction(
                user_id=user_id,
                amount=Decimal(f"{100 + i * 10}.00"),
                currency="INR",
                txn_date=base_date - timedelta(days=i, seconds=1),
                status="paid",
            )
        )

    async with db_session.begin():
        db_session.add_all(txns)
        await db_session.commit()

    return user_id, txns


async def test_get_transactions_for_user(
    client: AsyncClient, seed_transactions, fixed_utc_now: datetime
):
    """Test fetching the first page of transactions for a specific user."""
    # Add a future to_date to ensure all seeded data is included, avoiding
    # timing issues with default date filters.
    user_id, _ = seed_transactions

    params = {
        "user_id": str(user_id),
        "limit": "10",
        "to_date": fixed_utc_now.isoformat().replace("+00:00", "Z"),
    }

    response = await client.get(f"/transactions?{urlencode(params)}")

    assert response.status_code == 200
    data = response.json()
    assert len(data["transactions"]) == 10
    assert data["cursor"] != ""

    # Verify transactions are sorted by date descending
    dates = [t["txn_date"] for t in data["transactions"]]
    assert dates == sorted(dates, reverse=True)


async def test_get_transactions_with_pagination(
    client: AsyncClient, seed_transactions, fixed_utc_now: datetime
):
    """Test that cursor-based pagination works correctly."""
    user_id, _ = seed_transactions
    params = {
        "user_id": str(user_id),
        "to_date": fixed_utc_now.isoformat().replace("+00:00", "Z"),
        "limit": "5",
    }

    # --- Get first page ---
    response1 = await client.get(f"/transactions?{urlencode(params)}")
    assert response1.status_code == 200
    data1 = response1.json()

    assert len(data1["transactions"]) == 5
    cursor = data1["cursor"]
    assert cursor

    # --- Get second page ---
    params["cursor"] = cursor
    response2 = await client.get(f"/transactions?{urlencode(params)}")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["transactions"]) == 5

    # --- Verify pages are distinct ---
    ids1 = {t["id"] for t in data1["transactions"]}
    ids2 = {t["id"] for t in data2["transactions"]}
    assert not ids1.intersection(ids2)


async def test_get_transactions_with_date_filter(
    client: AsyncClient, seed_transactions, fixed_utc_now: datetime
):
    """Test filtering transactions by a specific date range."""
    user_id, _ = seed_transactions
    # Use the fixed_utc_now fixture for deterministic date calculations
    # We expect transactions from 5 to 10 days ago (inclusive).
    # Adjust the range to be inclusive of the exact timestamps created in the fixture.
    # The seeded data is `base_date - timedelta(days=i, seconds=1)`.
    to_date = (
        (fixed_utc_now - timedelta(days=5, seconds=1))
        .isoformat()
        .replace("+00:00", "Z")
    )
    from_date = (
        (fixed_utc_now - timedelta(days=10, seconds=1))
        .isoformat()
        .replace("+00:00", "Z")
    )

    params = {
        "user_id": str(user_id),
        "from_date": from_date,
        "to_date": to_date,
    }

    response = await client.get(f"/transactions?{urlencode(params)}")

    assert response.status_code == 200
    data = response.json()
    # Should be 6 transactions: for days 5, 6, 7, 8, 9, 10 ago.
    assert len(data["transactions"]) == 6


async def test_get_transactions_with_amount_filter(
    client: AsyncClient, seed_transactions, fixed_utc_now: datetime
):
    """Test filtering transactions by a minimum and maximum amount."""
    user_id, _ = seed_transactions
    # Amounts are 100, 110, ..., 290. This should get 150, 160, 170, 180, 190.
    min_amount = 150
    max_amount = 195
    to_date = fixed_utc_now.isoformat().replace("+00:00", "Z")

    params = {
        "user_id": str(user_id),
        "min_amount": str(min_amount),
        "max_amount": str(max_amount),
    }

    params["to_date"] = to_date
    response = await client.get(f"/transactions?{urlencode(params)}")

    assert response.status_code == 200
    data = response.json()
    assert len(data["transactions"]) == 5
    for txn in data["transactions"]:
        assert min_amount <= float(txn["amount"]) <= max_amount
