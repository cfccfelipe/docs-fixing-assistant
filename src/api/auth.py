import logging
from fastapi import Header, HTTPException, status

from api.config import settings

logger = logging.getLogger(__name__)

# --- 0. SECURITY & AUTHENTICATION ---


async def api_key_auth(x_api_key: str = Header(None, alias="X-API-KEY")):
    """
    Surgical API Key validation.
    Ensures that only authorized clients can access the orchestrator.
    """
    if not x_api_key or x_api_key != settings.API_KEY:
        logger.warning(f"🚫 Unauthorized access attempt with key: {x_api_key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return x_api_key
