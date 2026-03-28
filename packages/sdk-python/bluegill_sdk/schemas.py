from pydantic import BaseModel

class SessionIdRequest(BaseModel):
    session_id: str
    
class GenerateRequest(BaseModel):
    provider: str
    model: str
    session_id: str
    prompt: str