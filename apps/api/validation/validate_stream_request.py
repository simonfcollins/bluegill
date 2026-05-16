from fastapi import HTTPException
from bluegill_shared.models import StreamRequest
from bluegill_agent import MIN_WINDOW, InvalidProviderError, ProviderFactory

from api.service.session_manager import SessionManager
from api.helper.try_session_manager import try_session_manager

async def validate_stream_request(payload: StreamRequest, sm: SessionManager) -> None:
    """
    Validates attributes of the given StreamRequest.
    Raises an appropriate FastAPI HTTPException if any attribute is invalid.
    """
    
    session = try_session_manager(sm.get_session, session_id=payload.session_id)
    
    if not session:
        raise HTTPException(
            status_code=404, 
            detail=f"session does not exist with id '{payload.session_id}'"
        )

    if payload.window < MIN_WINDOW:
        raise HTTPException(
            status_code=400,
            detail=f"context window must be >= {MIN_WINDOW}"
        )
        
    if not payload.prompt or not payload.prompt.strip():
        raise HTTPException(
            status_code=422,
            detail="prompt cannot be an empty string"
        )
        
    try:
        provider = ProviderFactory.get_provider(payload.provider)
    except InvalidProviderError:
        raise HTTPException(
            status_code=400,
            detail=f"'{payload.provider}' is not a valid provider"
        )
        
    if not await provider.model_exists(payload.model):
        raise HTTPException(
            status_code=404,
            detail=f"model '{payload.model}' not found"
        )
