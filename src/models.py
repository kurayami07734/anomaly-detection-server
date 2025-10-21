import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from pydantic import BaseModel
from sqlalchemy import JSON, TIMESTAMP, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlmodel import Column, Field, SQLModel


class TransactionBase(SQLModel):
    user_id: uuid.UUID
    amount: Decimal = Field(max_digits=20, decimal_places=2)
    currency: str = Field(max_length=3)
    txn_date: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    status: str = Field(max_length=32)
    meta_data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB().with_variant(JSON, "sqlite"), nullable=True),
    )


class Transaction(TransactionBase, table=True):
    """Database model with UUID primary key"""

    __tablename__ = "transactions"

    # Composite index for the primary query pattern
    __table_args__ = (
        Index("ix_user_date_amount_id", "user_id", "txn_date", "amount", "id"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    user_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))


class TransactionFilters(BaseModel):
    user_id: uuid.UUID
    from_date: datetime | None = datetime.now(tz=UTC) - timedelta(days=30)
    to_date: datetime | None = datetime.now(tz=UTC)
    min_amount: Decimal | None = Decimal("0.00")
    max_amount: Decimal | None = Decimal("10000000000.00")
    limit: int | None = 100
    cursor: str | None = None


class ListTransactionsResponse(BaseModel):
    transactions: list[Transaction]
    cursor: str


class ListUsersResponse(BaseModel):
    users: list[uuid.UUID]
