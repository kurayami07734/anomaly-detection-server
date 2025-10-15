from typing import AsyncGenerator

import redis.asyncio as redis

from src.config import CONFIG


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """
    Dependency to get a Redis client.
    Ensures the client is always closed after the request.
    """
    redis_client = redis.from_url(
        CONFIG.REDIS_URL, encoding="utf-8", decode_responses=True
    )
    try:
        yield redis_client
    finally:
        await redis_client.close()
