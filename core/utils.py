import httpx
from fastapi import HTTPException
from tenacity import retry, stop_after_attempt, wait_fixed
import pybreaker
from cachetools import TTLCache

# Circuit breaker configuration
circuit_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)

# Cache configuration
cache = TTLCache(maxsize=1024, ttl=60)

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
@circuit_breaker
async def forward_request(url: str, method: str, headers: dict, data: dict = None, params: dict = None):
    """
    Forwards the request to the specified URL. Includes retry logic and circuit breaker.
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
            # Cache the response
            cache[url] = response.json()
            return response.json(), response.status_code
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Error communicating with upstream: {e}")
        elif e.response.status_code == 500:
            raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
        else:
            raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error: {e}")
    except pybreaker.CircuitBreakerError:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable due to circuit breaker")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Error communicating with upstream: {e}")

async def check_service_health(url: str):
    """
    Performs a health check for a given service
    """
    try:
       async with httpx.AsyncClient() as client:
          response = await client.get(url)
          response.raise_for_status()
          return True
    except httpx.HTTPError:
        return False
