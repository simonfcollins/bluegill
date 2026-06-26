from contextlib import asynccontextmanager
from typing import AsyncIterator, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from bluegill_shared.models import Message, Session, StreamRequest, AgentStreamResponse, NewSessionRequest
from bluegill_shared.utils import load_config, Workspace, Model, Config, Provider

from api.service.session_manager import SessionManager
from api.service.agent_service import AgentService
from api.repository.message_repository import MessageRepository
from api.repository.session_repository import SessionRepository
from api.exception.agent_service_exception import AgentServiceError
from api.validation.validate_stream_request import validate_stream_request
from api.helper.try_session_manager import try_session_manager
from api.service.workspace_registry import WorkspaceRegistry


CONFIG_PATH = Path("~/.bluegill/config.json").expanduser().resolve()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    FastAPI context manager. Initializes workspaces and session manager.
    """
    
    sm = SessionManager(SessionRepository(), MessageRepository())
    cfg = load_config(CONFIG_PATH)
    wr = WorkspaceRegistry(list(cfg.workspaces.values()), Path("/home/assistant/workspaces"))
    
    app.state.session_manager = sm
    app.state.config = cfg
    app.state.workspace_registry = wr
    app.state.agent_service = AgentService(sm, cfg, wr)
    
    yield
    
    
app = FastAPI(lifespan=lifespan)
    

@app.post("/stream", response_model=None)
async def stream(payload: StreamRequest, request: Request) -> StreamingResponse:
    """
    Stream responses and tool calls from the agent.
    """
    
    sm = request.app.state.session_manager
    cfg = request.app.state.config
    agent_service = request.app.state.agent_service
    
    await validate_stream_request(payload, sm, cfg)

    try:
        return StreamingResponse(await agent_service.chat_stream(payload), media_type="application/x-ndjson")
    
    except AgentServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate")
async def generate(payload: StreamRequest, request: Request) -> AgentStreamResponse:
    """
    Generates a single response with the given prompt and model/provider.
    """
    
    sm = request.app.state.session_manager
    cfg = request.app.state.config
    agent_service = request.app.state.agent_service
    
    await validate_stream_request(payload, sm, cfg)
    
    try:
        response = await agent_service.generate(payload)
        return response
    
    except AgentServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@app.get("/sessions")
async def get_sessions(request: Request) -> list[Session]:
    """
    Returns a list of all session IDs.
    """
    
    sm = request.app.state.session_manager

    return try_session_manager(sm.get_sessions)


@app.get("/sessions/last")
async def get_last_session(request: Request) -> Session:
    """
    Returns the last active session.
    """
    
    sm = request.app.state.session_manager
    
    session = try_session_manager(sm.load_last_session)
    
    if session == None:
        raise HTTPException(
            status_code=404, 
            detail="No sessions found. Create a new session using the '/sessions' POST endpoint"
        )
    
    return session


@app.get("/sessions/{session_id}")
async def get_session(session_id: str, request: Request) -> Session:
    """
    Get a session by session ID.
    """
    
    sm = request.app.state.session_manager
    
    session = try_session_manager(sm.get_session, session_id=session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session
    

@app.post("/sessions")
async def create_session(payload: NewSessionRequest, request: Request) -> Session:
    """
    Create a new session and return the session_id.
    """
    
    sm = request.app.state.session_manager

    return try_session_manager(sm.new_session, workspace_id=payload.workspace_id)


@app.post("/sessions/{session_id}/clear")
async def clear_session(session_id: str, request: Request) -> dict[str, str]:
    """
    Clears the current session context.
    Like /new but does not create a new session.
    """
    
    sm = request.app.state.session_manager
    
    try_session_manager(sm.clear_session, session_id=session_id)
    
    return {"status": "Session cleared"}


@app.get("/sessions/{session_id}/dump")
async def dump_session(session_id: str, request: Request) -> list[Message]:
    """
    Returns the specified sessions message chain.
    """
    
    sm = request.app.state.session_manager
    
    return try_session_manager(sm.get_messages, session_id=session_id)


@app.post("/sessions/{session_id}/compact")
async def compact(session_id: str, request: Request) -> dict[str, str]:
    """
    Compact the current session context.
    """
    
    sm = request.app.state.session_manager
    
    raise HTTPException(status_code=501, detail="Not implemented")


@app.get("/models")
async def get_models(request: Request) -> list[Model]:
    """
    Returns a list of models as listed in the config
    """
    
    return request.app.state.config.models


@app.get("/workspaces")
async def get_workspaces(request: Request) -> list[Workspace]:
    """
    Returns a list agent workspaces as listed in the config.
    """
    
    wr = request.app.state.workspace_registry
    
    return wr.workspaces

@app.get("/providers")
async def get_providers(request: Request) -> list[Provider]:
    """
    Returns as list of providers as listed in the config.
    """
    
    return list(request.app.state.config.providers.values())
        

@app.get("/config")
async def get_config(request: Request) -> Config:
    """
    Returns the loaded config object.
    """
    
    return request.app.state.config


@app.get("/status")
async def status(request: Request) -> dict[str, Any]:
    """
    Returns this service's ready status.
    """
    
    def not_ready(reason: str) -> None:
        raise HTTPException(
            status_code=503, 
            detail = {"status": "not_ready", "configured": False, "reason": reason}
        )
    
    if not get_providers(request):
        not_ready((
                    "Bad config: No providers detected.\n"
                    "Add a provider to config and reload service."
                ))

    if not get_models(request):
        not_ready((
                    "Bad config: No models detected.\n"
                    "Add a model to config and reload service."
                ))
        
    if not get_workspaces(request):
        not_ready((
                    "Bad config: No workspaces detected.\n"
                    "Add a workspace to config and reload service."
                ))
        
    return {"status": "ready", "configured": True}


@app.get("/health")
async def get_health() -> dict[str, str]:
    """
    Returns successfully if the service is running.
    """
    
    return {"status": "Service is running"}
    