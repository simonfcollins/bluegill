from fastapi import HTTPException
from bluegill_shared.models import StreamRequest
from bluegill_shared.utils import Config
from bluegill_agent import InvalidProviderError, ProviderFactory, ProviderError

from api.service.session_manager import SessionManager
from api.helper.try_session_manager import try_session_manager


async def validate_stream_request(payload: StreamRequest, sm: SessionManager, cfg: Config) -> None:
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
        
    if not payload.prompt or not payload.prompt.strip():
        raise HTTPException(
            status_code=422,
            detail="prompt cannot be an empty string"
        )
        
    try:
        provider = ProviderFactory.create(
            provider_name=payload.provider,
            base_url=cfg.providers[payload.provider].url
        )
        
    except InvalidProviderError:
        raise HTTPException(
            status_code=400,
            detail=f"'{payload.provider}' is not a valid provider"
        )
        
    try:
        if not await provider.model_exists(payload.model):
            raise HTTPException(
                status_code=404,
                detail=f"model '{payload.model}' not found"
            )

    except ProviderError as e:
        raise HTTPException(
            status_code=500,
            detail=f"error connecting to provider '{payload.provider}'"
        ) from e
