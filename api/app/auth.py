"""
API Key Authentication.
Both Raspberry and Laravel must send the header: X-API-Key
"""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from app.config import API_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verifies that the API Key is valid."""
    if not api_key or api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API Key",
        )
    return api_key
