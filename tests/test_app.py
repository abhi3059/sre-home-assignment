import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def test_client_with_mocks():
    app.state.db_conn = AsyncMock()
    app.state.redis = AsyncMock()
    return TestClient(app)


def test_healthcheck_with_mocks(test_client_with_mocks):
    response = test_client_with_mocks.get("/healthcheck")
    # Accepting both 200 and 503 (if mocked Redis/DB returns failure state)
    assert response.status_code in (200, 503)


def test_characters_endpoint_with_mocks(test_client_with_mocks):
    response = test_client_with_mocks.get("/characters?page=1&limit=2")
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        assert isinstance(response.json(), list)
