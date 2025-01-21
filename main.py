from contextlib import asynccontextmanager
from json import JSONDecodeError
from typing import Optional

from cachetools import TTLCache
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from loguru import logger
from pydantic import BaseModel
from redis import Redis

from config.config import config
from core.middleware import logging_middleware, tracing_middleware, transform_request_middleware
from core.security import authenticate
from core.utils import forward_request, check_service_health

from redis.asyncio import Redis
import h11
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # Setup Redis client
    redis_client = Redis.from_url(config.REDIS_URL)
    # Setup Rate Limiting
    await FastAPILimiter.init(redis_client)
    yield
    # Close Redis client
    await redis_client.close()


app = FastAPI(lifespan=lifespan,
              title="API Gateway",
              description="This is an API Gateway that forwards requests to downstream services",
              version="0.1",
              docs_url="/", )

# Setup Logging
logger.remove()
logger.add(lambda msg: print(msg, end=""), level="DEBUG" if config.DEBUG else "INFO")

# Setup Cache
cache = TTLCache(maxsize=1024, ttl=60)

# Apply Middlewares
app.middleware("http")(logging_middleware)
app.middleware("http")(tracing_middleware)
app.middleware("http")(transform_request_middleware)


class ServiceHealthResponse(BaseModel):
    service_a_healthy: bool
    service_b_healthy: bool


class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


@app.get("/items/{item_id}", dependencies=[Depends(RateLimiter(times=2, minutes=1))], operation_id="read_item")
async def read_item(item_id: int):
    if item_id in cache:
        logger.info(f"✅ Item: {item_id} found in the cache")
        return cache[item_id]

    logger.info(f"❌ Item: {item_id} NOT found in cache")
    # Return hard-coded example item to demonstrate caching
    item = Item(id=item_id, name=f"Example Item {item_id}", description="This is an example")
    cache[item_id] = item
    return item


@app.get(config.HEALTH_CHECK_PATH, response_model=ServiceHealthResponse, operation_id="health_check")
async def health_check():
    """
    Health check endpoint for the api gateway to check if the downstream services are running
    """
    service_a_healthy = await check_service_health(url=f"{config.SERVICE_A_URL}{config.HEALTH_CHECK_SERVICE_A}")
    service_b_healthy = await check_service_health(url=f"{config.SERVICE_B_URL}{config.HEALTH_CHECK_SERVICE_B}")
    return ServiceHealthResponse(service_a_healthy=service_a_healthy, service_b_healthy=service_b_healthy)


@app.exception_handler(h11._util.LocalProtocolError)
async def local_protocol_error_handler(request: Request, exc: h11._util.LocalProtocolError):
    logger.error(f"LocalProtocolError: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": "Too little data for declared Content-Length"},
    )


@app.api_route("/{path:path}", methods=["GET"], operation_id="gateway_get")
@app.api_route("/{path:path}", methods=["POST"], operation_id="gateway_post")
@app.api_route("/{path:path}", methods=["PUT"], operation_id="gateway_put")
@app.api_route("/{path:path}", methods=["DELETE"], operation_id="gateway_delete")
@app.api_route("/{path:path}", methods=["PATCH"], operation_id="gateway_patch")
async def gateway(path: str, request: Request, auth_payload: dict = Depends(authenticate)):
    """
    Main API Gateway function.
    """
    logger.debug(f"📥 Received request: {request.method} {request.url}")

    # Determine the backend URL based on path prefix (can be more sophisticated later)
    if path.startswith("service-a"):
        url = f"{config.SERVICE_A_URL}/{path.removeprefix('service-a/')}"
    elif path.startswith("service-b"):
        url = f"{config.SERVICE_B_URL}/{path.removeprefix('service-b/')}"
    else:
        raise HTTPException(status_code=404, detail="Service not found")

    # Construct headers (remove some headers that are meant for the gateway only)
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("connection", None)

    # Read request body as JSON if it exists (and it's not a GET request)
    json_body = None
    if request.method != "GET":
        try:
            json_body = await request.json()
        except JSONDecodeError:
            json_body = None

    # Handle query parameters
    params = dict(request.query_params)

    # Forward the request
    response_data, status_code = await forward_request(url=url, method=request.method, headers=headers, data=json_body,
                                                       params=params)

    logger.debug(f"📤 Forwarded request to {url}, status code: {status_code}")

    if not response_data:
        response_data = {}

    return JSONResponse(content=response_data, status_code=status_code)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=config.PORT)
