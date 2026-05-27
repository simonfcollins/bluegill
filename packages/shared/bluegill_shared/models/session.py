from pydantic import BaseModel

class Session(BaseModel):
    """
    Model representing an entity in the "sessions" table.
    
    Columns:
        id: Primary key. Hexidecimal UUID. Manually generate before insertion.

        name: A descriptive name for the session.

        tokens_used: The number of tokens in all messages + system prompt belonging to this session.

        created_at: Timestamp generated at time of row insertion.
    """
    
    id: str
    name: str
    tokens_used: int
    created_at: str | None= None
    