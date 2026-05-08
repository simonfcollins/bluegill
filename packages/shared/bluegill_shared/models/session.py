from pydantic import BaseModel

class Session(BaseModel):
    """
    Model representing an entity in the "sessions" table.
    
    Columns:
        id: Primary key. Hexidecimal UUID. Manually generate before insertion.

        name: A descriptive name for the session.

        created_at: Timestamp generated at time of row insertion.
    """
    
    id: str
    name: str
    created_at: str | None= None
    