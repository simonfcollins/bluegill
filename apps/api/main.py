from fastapi import FastAPI
from apps.api.schemas import LLMRequest, UpdateSessionRequest
from bluegill_agent.agent.agent import run_agent
from bluegill_agent.services.workspace_provider import WorkspaceProvider
from bluegill_agent.services.session_manager import session_manager
from bluegill_agent.entity.session import Session
from bluegill_agent.entity.message import Message
from typing import Any
import json

app = FastAPI()
WorkspaceProvider.initialize("/mnt/workspaces/")

@app.post("/query")
async def agent_endpoint(request: LLMRequest):
    result = await run_agent(
        request.provider,
        request.model,
        request.prompt,
        request.session_id
    )
    return {"response": result}


@app.post("/new")
async def create_session() -> dict[str, str]:
    """
    Create a new session and return the session_id.
    """
    session = session_manager.new_session()
    return {"session_id": session.id}


@app.post("/clear")
async def clear_session(request: UpdateSessionRequest) -> dict[str, str]:
    """
    Clears the current session context.
    Like /new but does not create a new session.
    """
    session_manager.clear_session(request.session_id)
    return {"status": "Session cleared."}


@app.post("/compact")
async def compact(request: UpdateSessionRequest) -> dict[str, str]:
    """
    Compact the current session context.
    """
    return {"status": "Not implemented."}


@app.get("/dump")
async def dump_session(session_id: str) -> list[Message]:
    """
    Returns the specified sessions message chain.
    """
    return session_manager.get_messages(session_id)
    
    
@app.get("/history")
async def get_conversation_history(session_id: str) -> list[Message]:
    """
    Returns all messages between the assistant and user.
    """
    messages = session_manager.get_messages(session_id)
    conversation = []
    for m in messages:
        try:
            data = json.loads(m.content)
            has_tool = "tool" in data
        except Exception:
            has_tool = False
            
        if (m.role == "assistant" and not has_tool) or m.role == "user":
            conversation.append(m)
            
    return conversation
    
    
@app.get("/sessions")
async def get_sessions() -> list[Session]:
    """
    Returns a list of all session IDs.
    """
    return session_manager.get_sessions()


@app.get("/last")
async def get_last_session() -> Session:
    """
    Returns the last active session.
    """
    return session_manager.load_last_session()
