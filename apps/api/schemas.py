from pydantic import BaseModel

class LLMRequest(BaseModel):
    provider: str
    model: str
    prompt: str
    session_id: str

class UpdateSessionRequest(BaseModel):
    session_id: str