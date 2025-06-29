import pytest
import os
import json
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

os.environ["OTEL_SDK_DISABLED"] = "true"
from app.main import app

@pytest.fixture
def test_client_with_mocks():
    app.state.db_conn = AsyncMock()

    mock_redis = AsyncMock()
    mock_data = json.dumps([
        {
            "id": 1,
            "name": "Rick Sanchez",
            "status": "Alive",
            "species": "Human",
            "origin": "Earth (C-137)"
        },
        {
            "id": 2,
            "name": "Morty Smith",
            "status": "Alive",
            "species": "Human",
            "origin": "Earth (C-137)"
        }
    ])
    mock_redis.get.return_value = mock_data
    mock_redis.setex.return_value = True

    app.state.redis = mock_redis
    return TestClient(app)


def test_healthcheck_with_mocks(test_client_with_mocks):
    response = test_client_with_mocks.get("/healthcheck")
    assert response.status_code in (200, 503)


def test_characters_endpoint_with_mocks(test_client_with_mocks):
    response = test_client_with_mocks.get("/characters?page=1&limit=2")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2
