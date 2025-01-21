import httpx
import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis
from tenacity import retry, stop_after_attempt, wait_fixed

from config.config import config
from main import app


@pytest.fixture(scope="session")
async def setup_limiter():
    """Initializes the Rate limiter."""
    redis = Redis.from_url(config.REDIS_URL)
    await FastAPILimiter.init(redis)
    yield redis
    await redis.close()


@pytest.fixture(scope="session")
def client(setup_limiter):
    """Initialize a test client with FastAPILimiter initialized in a test fixture."""
    return TestClient(app)


def get_auth_token():
    payload = {"sub": "test_user"}
    token = jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return f"Bearer {token}"


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
async def forward_request(url: str, method: str, headers: dict, data: dict = None, params: dict = None):
    """
    Forwards the request to the specified URL. Includes retry logic.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
            )
            response.raise_for_status()
            return response.json(), response.status_code
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Error communicating with upstream: {e}")
        raise


def test_health_check_returns_service_status(client):
    response = client.get("/health")
    assert response.status_code == 200
    if response.content:
        assert response.json() == {"service_a_healthy": True, "service_b_healthy": True}
    else:
        assert response.json() == {}


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


def test_gateway_get_returns_401_for_missing_auth(client):
    response = client.get("/service-a/some-path")
    assert response.status_code == 401


def test_gateway_post_returns_401_for_missing_auth(client):
    response = client.post("/service-a/some-path", json={"key": "value"})
    assert response.status_code == 401


def test_gateway_put_returns_401_for_missing_auth(client):
    response = client.put("/service-a/some-path", json={"key": "value"})
    assert response.status_code == 401


def test_gateway_delete_returns_401_for_missing_auth(client):
    response = client.delete("/service-a/some-path")
    assert response.status_code == 401


def test_gateway_patch_returns_401_for_missing_auth(client):
    response = client.patch("/service-a/some-path", json={"key": "value"})
    assert response.status_code == 401


def test_gateway_invalid_path(client):
    headers = {"Authorization": get_auth_token()}
    response = client.get("/invalid-path", headers=headers)
    assert response.status_code == 404  # Not Found


def test_gateway_invalid_method(client):
    headers = {"Authorization": get_auth_token()}
    response = client.head("/service-a/some-path", headers=headers)
    assert response.status_code == 405


def test_gateway_invalid_service(client):
    headers = {"Authorization": get_auth_token()}
    response = client.get("/service-c/some-path", headers=headers)
    assert response.status_code == 404  # Not Found


def test_gateway_get_missing_required_fields(client):
    headers = {"Authorization": get_auth_token()}
    response = client.get("/service-a/some-path", headers=headers)
    assert response.status_code == 200
    if response.content:
        assert response.json() == {"message": "This is service-a"}
    else:
        assert response.json() == {}


def test_gateway_post_missing_required_fields(client):
    headers = {"Authorization": get_auth_token()}
    response = client.post("/service-a/some-path", json={}, headers=headers)
    assert response.status_code == 200
    if response.content:
        assert response.json() == {"message": "POST request to service-a", "data": {}}
    else:
        assert response.json() == {}


def test_too_little_data_for_declared_content_length_error(client):
    headers = {"Authorization": get_auth_token(), "Content-Length": "100"}
    response = client.post("/service-a/some-path", headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Too little data for declared Content-Length"}
