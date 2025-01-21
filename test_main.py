import jwt
import pytest
from fastapi.testclient import TestClient
from src.config import config
from src.main import app

@pytest.fixture
def client():
    """
    Initialize a test client.
    """
    return TestClient(app)

def get_auth_token():
    payload = {"sub": "test_user"}
    token = jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return f"Bearer {token}"

def test_read_item_returns_cached_item(client):
    response = client.get("/items/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

def test_read_item_returns_new_item(client):
    response = client.get("/items/2")
    assert response.status_code == 200
    assert response.json()["id"] == 2

def test_health_check_returns_service_status(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "service_a_healthy" in response.json()
    assert "service_b_healthy" in response.json()

def test_gateway_get_returns_200_or_404(client):
    headers = {"Authorization": get_auth_token()}
    response = client.get("/service-a/some-path", headers=headers)
    assert response.status_code in [200, 404]

def test_gateway_post_returns_200_or_404(client):
    headers = {"Authorization": get_auth_token()}
    response = client.post("/service-a/some-path", json={"key": "value"}, headers=headers)
    assert response.status_code in [200, 404]

def test_gateway_put_returns_200_or_404(client):
    headers = {"Authorization": get_auth_token()}
    response = client.put("/service-a/some-path", json={"key": "value"}, headers=headers)
    assert response.status_code in [200, 404]

def test_gateway_delete_returns_200_or_404(client):
    headers = {"Authorization": get_auth_token()}
    response = client.delete("/service-a/some-path", headers=headers)
    assert response.status_code in [200, 404]

def test_gateway_patch_returns_200_or_404(client):
    headers = {"Authorization": get_auth_token()}
    response = client.patch("/service-a/some-path", json={"key": "value"}, headers=headers)
    assert response.status_code in [200, 404]
