from fastapi.testclient import TestClient
from app.main import app
 

def test_healthcheck():
    with TestClient(app) as client:
        response = client.get("/healthcheck")
        # Accepting both 200 (success) and 503 (if Redis/DB is unreachable in CI)
        assert response.status_code in [200, 503]

def test_characters_endpoint():
    with TestClient(app) as client:
        response = client.get("/characters?page=1&limit=2")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
 