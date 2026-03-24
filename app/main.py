from fastapi import FastAPI
from app.schemas import LLMRequest
from app.agent.agent import run_agent
from app.services.session_manager import session_manager
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

@app.post("/query")
async def agent_endpoint(request: LLMRequest):
    session_id = session_manager.current_session_id or session_manager.new_session()
    
    result = await run_agent(
        request.provider,
        request.model,
        request.prompt,
        session_id
    )
    return {"response": result}

@app.post("/new")
async def create_session():
    """
    Create a new session and return the session_id.
    """
    session_id = session_manager.new_session()
    return {"session_id": session_id}