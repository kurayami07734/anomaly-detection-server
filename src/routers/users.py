import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import distinct, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.models import ListUsersResponse, Transaction

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/users", response_model=ListUsersResponse)
async def get_users(db: AsyncSession = Depends(get_session)):
    """
    Returns a list of all unique user IDs present in the transactions table.
    """
    try:
        result = await db.execute(select(distinct(Transaction.user_id)))
        user_ids = result.scalars().all()
        return {"users": user_ids}
    except SQLAlchemyError:
        logger.exception("Error fetching user IDs")
        raise HTTPException(
            status_code=500, detail="Could not fetch user IDs from the database."
        )
