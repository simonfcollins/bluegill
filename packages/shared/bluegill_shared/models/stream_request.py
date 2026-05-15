from pydantic import BaseModel

class StreamRequest(BaseModel):
    """
    Represents the body of the '/stream' POST endpoint of the Bluegill API.
    
    Attributes:
        provider: A valid LLM provider name.
        
        model: A model name (e.g. 'qwen3.5:9b').
        
        window: The context window size. Defaults to 8000 tokens.
        
        session_id: A valid session id. Messages generated in this request will be added to the given session.
        
        prompt: The user's prompt.
    """
    
    provider: str
    model: str
    window: int = 8000
    session_id: str
    prompt: str
