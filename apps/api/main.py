from fastapi import FastAPI
from apps.api.schemas import LLMRequest, UpdateSessionRequest
from bluegill_agent.agent.agent import run_agent
from bluegill_agent.services.workspace_provider import WorkspaceProvider
from bluegill_agent.services.session_manager import session_manager

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
async def create_session():
    """
    Create a new session and return the session_id.
    """
    session_id = session_manager.new_session()
    return {"session_id": session_id}


@app.post("/clear")
async def clear_session(request: UpdateSessionRequest):
    """
    Clears the current session context.
    Like /new but does not create a new session.
    """
    session_manager.clear_session(request.session_id)
    return {"status": "Session cleared."}


@app.post("/compact")
async def compact(request: UpdateSessionRequest):
    """
    Compact the current session context.
    """
    return {"status": "Not implemented."}


@app.get("/dump")
async def dump_session(session_id: str):
    """
    Returns the specified sessions message chain.
    """
    messages = session_manager.get_messages(session_id, limit=1000)
    return {"messages": messages}
    
    
@app.get("/sessions")
async def get_sessions():
    """
    Returns a list of all session IDs.
    """
    sessions = session_manager.get_sessions()
    return {"sessions": sessions}


@app.get("/last")
async def get_last_session():
    """
    Returns the last active session.
    """
    session_id = session_manager.load_last_session()
    return {"session_id": session_id}