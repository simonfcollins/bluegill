from pydantic import BaseModel

class LLMStreamResponse(BaseModel):
    """
    A normalized streaming chunk of output from an LLM provider, 
    containing partial generation results and completion metadata.
    
    Attributes:
        model: Name of the model used to generate the response.
        
        created_at: The timestamp in UTC of when this chunk was created.
    
        response: empty if the response was streamed, if not streamed, 
                   this will contain the full response.
                   
        done: True if this is the last chunk in the stream. False otherwise.

        total_duration: Time spent generating the response.
        
        token_count: The total number of tokens used in the prompt and response.
    """
    
    model: str
    created_at: str
    response: str = ""
    done: bool = False
    total_duration: int | None = None
    token_count: int | None = None
    