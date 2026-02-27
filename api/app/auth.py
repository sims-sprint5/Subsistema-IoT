"""
Autenticación por API Key.
Tanto la Raspberry como Laravel deben enviar el header: X-API-Key
"""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from app.config import API_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verifica que el API Key sea válido."""
    if not api_key or api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="API Key inválida o no proporcionada",
        )
    return api_key
