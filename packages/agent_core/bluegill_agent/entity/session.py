from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Session(BaseModel):
    """
    Model representing an entity in the "sessions" table.
    
    Columns:
        id - Primary key. Hexidecimal UUID. Manually generate before insertion.
        name - A descriptive name for the session.
        created_at - Timestamp generated at time of row insertion.
    """
    
    id: str
    name: str
    created_at: Optional[datetime] = None
    