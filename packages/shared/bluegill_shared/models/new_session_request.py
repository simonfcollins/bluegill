from pydantic import BaseModel

class NewSessionRequest(BaseModel):
    workspace_id: str
