import uuid

from httpx import AsyncClient

from tests.conftest import USERS


async def test_get_users(client: AsyncClient):
    response = await client.get("/users")
    data = response.json()
    # Convert string UUIDs from JSON back to UUID objects for comparison
    users = {uuid.UUID(u) for u in data["users"]}

    assert response.status_code == 200
    assert users == set(USERS)
