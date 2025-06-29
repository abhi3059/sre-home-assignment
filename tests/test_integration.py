import requests

def test_api_live():
    r = requests.get("http://localhost:8000/characters?page=1&limit=1")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
