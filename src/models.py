from typing import Optional, Any
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid

from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import TIMESTAMP, Index, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB


class TransactionBase(SQLModel):
    user_id: uuid.UUID
    amount: Decimal = Field(max_digits=20, decimal_places=2)
    currency: str = Field(max_length=3)
    txn_date: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    status: str = Field(max_length=32)
    meta_data: Optional[dict[str, Any]] = Field(
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
    from_date: Optional[datetime] = datetime.now(tz=timezone.utc) - timedelta(days=30)
    to_date: Optional[datetime] = datetime.now(tz=timezone.utc)
    min_amount: Optional[Decimal] = Decimal("0.00")
    max_amount: Optional[Decimal] = Decimal("10000000000.00")
    limit: Optional[int] = 100
    cursor: Optional[str] = None


class ListTransactionsResponse(BaseModel):
    transactions: list[Transaction]
    cursor: str


class ListUsersResponse(BaseModel):
    users: list[uuid.UUID]
