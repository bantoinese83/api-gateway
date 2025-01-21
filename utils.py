import httpx
from fastapi import HTTPException
from tenacity import retry, stop_after_attempt, wait_fixed

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