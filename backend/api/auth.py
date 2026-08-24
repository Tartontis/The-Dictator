from fastapi import Header, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED

import secrets
from backend.config import Settings, load_settings

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_settings():
    """Dependency to get application settings."""
    return load_settings()

def verify_api_key(
    api_key: str = Security(api_key_header),
    settings: Settings = Depends(get_settings)
):
    """
    Verify the API key if one is configured.
    If no API key is configured, allow all requests.
    """
    configured_api_key = settings.server.api_key

    if not configured_api_key:
        return None

    if not api_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API Key missing"
        )

    if not secrets.compare_digest(api_key, configured_api_key):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Could not validate API Key"
        )

    return api_key
