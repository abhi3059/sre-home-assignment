import pytest
import requests

def is_api_up():
    try:
        response = requests.get("http://localhost:8000/healthcheck", timeout=1)
        return response.status_code in (200, 503)
    except Exception:
        return False

@pytest.mark.skipif(not is_api_up(), reason="API is not running on localhost:8000")
def test_api_live():
    response = requests.get("http://localhost:8000/characters?page=1&limit=1", timeout=5)
    assert response.status_code == 200
