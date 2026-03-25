import pytest
from httpx import AsyncClient
from httpx import ASGITransport
from fastapi import status
from src.app import app
import copy

# Use a fixture to reset the in-memory activities data before each test
@pytest.fixture(autouse=True)
def reset_activities(monkeypatch):
    from src import app as app_module
    orig_activities = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(orig_activities))

@pytest.mark.asyncio
async def test_get_activities():
    # Arrange
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Act
        response = await ac.get("/activities")
    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]

@pytest.mark.asyncio
async def test_signup_success():
    # Arrange
    test_email = "newstudent@mergington.edu"
    activity = "Chess Club"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Act
        response = await ac.post(f"/activities/{activity}/signup?email={test_email}")
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert f"Signed up {test_email} for {activity}" in response.json()["message"]
        # Confirm participant added
        get_resp = await ac.get("/activities")
        assert test_email in get_resp.json()[activity]["participants"]

@pytest.mark.asyncio
async def test_signup_duplicate():
    # Arrange
    activity = "Chess Club"
    existing_email = "michael@mergington.edu"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Act
        response = await ac.post(f"/activities/{activity}/signup?email={existing_email}")
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already signed up" in response.json()["detail"]

@pytest.mark.asyncio
async def test_signup_nonexistent_activity():
    # Arrange
    activity = "Nonexistent Club"
    email = "someone@mergington.edu"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Act
        response = await ac.post(f"/activities/{activity}/signup?email={email}")
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Activity not found" in response.json()["detail"]
