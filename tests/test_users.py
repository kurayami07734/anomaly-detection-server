import uuid
from fastapi.testclient import TestClient
from tests.conftest import USERS


def test_get_users(client: TestClient):
    response = client.get("/users")
    data = response.json()
    # Convert string UUIDs from JSON back to UUID objects for comparison
    users = {uuid.UUID(u) for u in data["users"]}

    assert response.status_code == 200
    assert users == set(USERS)
