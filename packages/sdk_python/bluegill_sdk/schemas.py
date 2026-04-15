from pydantic import BaseModel

class SessionIdRequest(BaseModel):
    session_id: str
    
class GenerateRequest(BaseModel):
    provider: str
    model: str
    session_id: str
    prompt: str
    
class Message(BaseModel):
    role: str
    content: str
    created_at: str

class Session(BaseModel):
    id: str
    name: str
