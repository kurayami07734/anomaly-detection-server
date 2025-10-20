from typing import Annotated
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import desc, select

from src.database import get_session
from src.models import Transaction, TransactionFilters, ListTransactionsResponse
from src.utils import decode_base64, encode_base64

router = APIRouter()


@router.get("/transactions", response_model=ListTransactionsResponse)
async def get_transactions(
    params: Annotated[TransactionFilters, Query(...)],
    db: AsyncSession = Depends(get_session),
):
    try:
        conditions = [
            Transaction.user_id == params.user_id,
            Transaction.txn_date >= params.from_date,
            Transaction.txn_date <= params.to_date,
            Transaction.amount >= params.min_amount,
            Transaction.amount <= params.max_amount,
        ]

        if params.cursor:
            cursor_data = decode_base64(params.cursor)
            cursor_date = datetime.fromisoformat(cursor_data["txn_date"])
            cursor_id = uuid.UUID(cursor_data["id"])
            conditions.append(
                (Transaction.txn_date < cursor_date)
                | ((Transaction.txn_date == cursor_date) & (Transaction.id < cursor_id))
            )

        query = (
            select(Transaction)
            .where(*conditions)
            .limit(params.limit)
            .order_by(desc(Transaction.txn_date), asc(Transaction.id))
        )

        txns = list((await db.execute(query)).scalars().all())

        cursor = (
            encode_base64(
                {
                    "txn_date": txns[-1].txn_date.isoformat(),
                    "id": str(txns[-1].id),
                }
            )
            if txns
            else ""
        )

        return ListTransactionsResponse(transactions=txns, cursor=cursor)
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return ListTransactionsResponse(transactions=[], cursor="")
