from typing import List
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.models import Transaction, ListUsersResponse

router = APIRouter()


@router.get("/users", response_model=ListUsersResponse)
async def get_users(db: AsyncSession = Depends(get_session)):
    """
    Returns a list of all unique user IDs present in the transactions table.
    """
    result = await db.execute(select(distinct(Transaction.user_id)))
    user_ids = result.scalars().all()
    return {"users": user_ids}
