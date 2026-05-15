from typing import Literal
from pydantic import BaseModel

Role = Literal["user", "assistant", "tool", "system"]


class Message(BaseModel):
    """
    Model representing an entity in the "messages" table.
    
    Columns:
        id: Auto-incremented primary key.
        
        session_id: Foreign key of the session this message belongs to.
        
        role: The source of the message ("user", "assistant", "tool", "system").
        
        content: The content of the message such as a user prompt or assistant response.
        
        created_at: Timestamp generated at time of row insertion.
    """
    
    id: int | None = None
    session_id: str | None = None
    role: Role
    content: str
    created_at: str | None = None
