from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_healthcheck():
    response = client.get("/healthcheck")
    assert response.status_code == 200

def test_characters_endpoint():
    response = client.get("/characters?page=1&limit=2")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

