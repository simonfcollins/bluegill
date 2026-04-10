from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Message(BaseModel):
    """
    Model representing an entity in the "messages" table.
    
    Columns:
        id - Auto-incremented primary key
        session_id - Foreign key of the session this message belongs to
        role - The source of the message ("user", "assistant", "system", "tool")
        content - The content of the message such as a user prompt or assistant response
        created_at - Timestamp generated at time of row insertion.
    """
    
    id: Optional[int] = None
    session_id: Optional[str]
    role: str
    content: str
    created_at: Optional[datetime] = None