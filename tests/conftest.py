import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(autouse=True)
def mock_state(monkeypatch):
    app.state.db_conn = None
    app.state.redis = None
    yield
