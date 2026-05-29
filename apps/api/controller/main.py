from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from bluegill_agent import WorkspaceProvider
from bluegill_shared.models import Message, Session, StreamRequest, AgentStreamResponse

from api.service.session_manager import SessionManager
from api.service.agent_service import AgentService
from api.repository.message_repository import MessageRepository
from api.repository.session_repository import SessionRepository
from api.exception.session_manager_exception import SessionManagerError
from api.exception.agent_service_exception import AgentServiceError
from api.validation.validate_stream_request import validate_stream_request
from api.helper.try_session_manager import try_session_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    FastAPI context manager. Initializes workspaces and session manager.
    """
    
    WorkspaceProvider.initialize("~/workspaces")
    app.state.session_manager = SessionManager(SessionRepository(), MessageRepository())
    app.state.agent_service = AgentService(app.state.session_manager)
    
    yield
    
    
app = FastAPI(lifespan=lifespan)
    

@app.post("/stream", response_model=None)
async def stream(payload: StreamRequest, request: Request) -> StreamingResponse:
    """
    Stream responses and tool calls from the agent.
    """
    
    sm = request.app.state.session_manager
    agent_service = request.app.state.agent_service
    
    await validate_stream_request(payload, sm)

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
    agent_service = request.app.state.agent_service
    
    await validate_stream_request(payload, sm)
    
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
    
    return try_session_manager(sm.load_last_session)


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
async def create_session(request: Request) -> Session:
    """
    Create a new session and return the session_id.
    """
    
    sm = request.app.state.session_manager
    
    return try_session_manager(sm.new_session)


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
        