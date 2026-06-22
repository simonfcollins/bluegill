from pydantic import BaseModel

class LLMStreamResponse(BaseModel):
    """
    A normalized streaming chunk of output from an LLM provider, 
    containing partial generation results and completion metadata.
    
    Attributes:
        model: Name of the model used to generate the response.
        
        created_at: The timestamp in UTC of when this chunk was created.
    
        response: The final generated response from the model.
                   
        thinking: The model's thinking if requested. 
                   
        done: True if this is the last chunk in the stream. False otherwise.

        total_duration: Time spent generating the response.
        
        token_count: The total number of tokens used in the prompt and response.
    """
    
    model: str
    created_at: str
    response: str = ""
    thinking: str | None = None
    done: bool = False
    total_duration: int | None = None
    token_count: int | None = None
    