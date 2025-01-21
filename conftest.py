import pytest
from fastapi.testclient import TestClient
from config import config
from main import app


@pytest.fixture(scope="session")
def event_loop():
    """
    Overrides the default pytest event loop
    """
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def setup_limiter():
    """
    Initializes the Rate limiter.
    """
    from fastapi_limiter import FastAPILimiter
    from redis.asyncio import Redis
    redis = Redis.from_url(config.REDIS_URL)
    await FastAPILimiter.init(redis)
    yield
    await redis.close()

@pytest.fixture(scope="session")
async def client(setup_limiter):
    """
    Initialize a test client with FastAPILimiter initialized in a test fixture.
    """
    await setup_limiter
    return TestClient(app)
