from pydantic import BaseModel

class StreamRequest(BaseModel):
    """
    Represents the body of the '/stream' POST endpoint of the Bluegill API.
    
    Attributes:
        provider: A valid LLM provider name.
        
        model: A model name (e.g. 'qwen3.5:9b').
        
        session_id: A valid session id. Messages generated in this request will be added to the given session.
        
        prompt: The user's prompt.
        
        think: True if the agent should show thinking. False otherwise.
    """
    
    provider: str
    model: str
    session_id: str
    prompt: str
    think: bool = False
