from fastapi.testclient import TestClient
from app.main import app
def test_home_page():
    response=TestClient(app).get('/')
    assert response.status_code == 200
    assert 'Long links' in response.text
