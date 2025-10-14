from typing import Optional, Any
from datetime import datetime
from decimal import Decimal
import uuid

from sqlmodel import Field, SQLModel, Column
from sqlalchemy import TIMESTAMP, Index
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
        default=None, sa_column=Column(JSONB, nullable=True)
    )


class Transaction(TransactionBase, table=True):
    """Database model with UUID primary key"""

    __tablename__ = "transactions"

    # Composite index for the primary query pattern
    __table_args__ = (Index("ix_user_date_id", "user_id", "txn_date", "id"),)

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    user_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), nullable=False))
