from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, AsyncIterator, Callable
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

from bluegill_agent import run_agent, WorkspaceProvider, InvalidProviderError, MIN_WINDOW, ProviderFactory

from bluegill_shared.models import Message, Session, StreamRequest, AgentStreamResponse

from api.util.logger import get_logger
from api.service.session_manager import SessionManager
from api.repository.message_repository import MessageRepository
from api.repository.session_repository import SessionRepository
from api.exception.session_manager_exception import SessionManagerError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    FastAPI context manager. Initializes workspaces and session manager.
    """
    
    WorkspaceProvider.initialize("~/workspaces")
    app.state.session_manager = SessionManager(SessionRepository(), MessageRepository())
    
    yield
    
    
app = FastAPI(lifespan=lifespan)
    

@app.post("/stream", response_model=None)
async def stream(payload: StreamRequest, request: Request) -> StreamingResponse:
    """
    Stream responses and tool calls from the agent.
    """
    
    sm = request.app.state.session_manager
    logger = get_logger(payload.session_id)
    
    try:
        # verify session exists
        if not sm.get_session(payload.session_id):
            raise HTTPException(
                status_code=404, 
                detail=f"session does not exist with id '{payload.session_id}'"
            )
    except SessionManagerError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
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
    
    try:
        # add user prompt to the session
        sm.add_message(
            session_id=payload.session_id,
            role="user",
            content=payload.prompt
        )
        logger.info(f"[USER] {payload.prompt}")
        messages = sm.get_messages(payload.session_id)
    except SessionManagerError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
    # stream generator function
    async def generator() -> AsyncGenerator[str, None]:
        async for chunk in run_agent( # run the agent
            payload.provider, 
            payload.model,
            messages,
            payload.window
        ):
            if chunk.event == "error":
                logger.error(f"[ERROR] {chunk.content}")

            if chunk.done and chunk.context: # if stream is done...
                new_messages = []
                for m in chunk.context[1]: # collect new messages
                    new_messages.append(Message(
                        role=m.role, 
                        content=m.content, 
                        session_id=payload.session_id
                    ))
                    # log conversation
                    log = logger.warning if m.role == "system" else logger.info
                    log(f"[{m.role.capitalize()}] {m.content}")

                if len(new_messages):
                    try:
                        # add new messages to session
                        sm.add_messages(new_messages)
                    except SessionManagerError as e:
                        logger.error(f"[ERROR] Failed to add new context to session")
                        
                        yield AgentStreamResponse(
                            event="error",
                            content=f"Failed to add new context to session: {e}"
                        ).model_dump_json(exclude_none=True) + "\n"
            
            # yield the agent response
            yield chunk.model_dump_json(exclude_none=True) + "\n"

    return StreamingResponse(generator(), media_type="application/x-ndjson")


@app.post("/new")
async def create_session(request: Request) -> dict[str, str]:
    """
    Create a new session and return the session_id.
    """
    
    sm = request.app.state.session_manager
    
    session = try_session_manager(sm.new_session)
        
    return {"session_id": session.id}


@app.post("/clear")
async def clear_session(session_id: str, request: Request) -> dict[str, str]:
    """
    Clears the current session context.
    Like /new but does not create a new session.
    """
    
    sm = request.app.state.session_manager
    
    try_session_manager(sm.clear_session, session_id=session_id)
    
    return {"status": "Session cleared"}


@app.post("/compact")
async def compact(session_id: str, request: Request) -> dict[str, str]:
    """
    Compact the current session context.
    """
    
    sm = request.app.state.session_manager
    
    raise HTTPException(status_code=501, detail="Not implemented")


@app.get("/dump")
async def dump_session(session_id: str, request: Request) -> list[Message]:
    """
    Returns the specified sessions message chain.
    """
    
    sm = request.app.state.session_manager
    
    return try_session_manager(sm.get_messages, session_id=session_id)
    
    
@app.get("/sessions")
async def get_sessions(request: Request) -> list[Session]:
    """
    Returns a list of all session IDs.
    """
    
    sm = request.app.state.session_manager

    return try_session_manager(sm.get_sessions)


@app.get("/last")
async def get_last_session(request: Request) -> Session:
    """
    Returns the last active session.
    """
    
    sm = request.app.state.session_manager
    
    return try_session_manager(sm.load_last_session)


def try_session_manager(fun: Callable[..., Any], **xargs: Any) -> Any:
    """
    Helper function that trys executing the given SessionManager method.
    Raises a FastAPI HTTPException if fun raises an error.
    """
    
    try:
        return fun(**xargs)
    except SessionManagerError as e:
        raise HTTPException(status_code=500, detail=str(e))
        