from pydantic import BaseModel

from bluegill_agent.schemas.llm_stream_response import LLMStreamResponse

class OllamaStreamResponse(BaseModel):
    """
    Respresents a single streamed chunk returned by the Ollama '/api/generate' endpoint
    when streaming is enabled.
    
    Attributes:
    
        model: Name of the model used to generate the response.
        
        created_at: The timestamp in UTC of when this chunk was created.
    
        response: empty if the response was streamed, if not streamed, 
                   this will contain the full response.
                   
        done: True if this is the last chunk in the stream. False otherwise.
        
        context: An encoding of the conversation used in this response, 
                  this can be sent in the next request to keep a conversational memory.

        total_duration: Time spent generating the response.
        
        load_duration: Time spent in nanoseconds loading the model.
        
        prompt_eval_count: Number of tokens in the prompt.
        
        prompt_eval_duration: Time spent in nanoseconds evaluating the prompt.
        
        eval_count: Number of tokens in the response.
        
        eval_duration: Time in nanoseconds spent generating the response.
        
    References:
        https://ollama.readthedocs.io/en/api/#response
    """
    
    model: str
    created_at: str
    response: str = ""
    done: bool = False
    context: list[int] | None = None
    total_duration: int | None = None
    load_duration: int | None = None
    prompt_eval_count: int | None = None
    prompt_eval_duration: int | None = None
    eval_count: int | None = None
    eval_duration: int | None = None
    
    
    def to_llm_stream_response(self) -> LLMStreamResponse:
        """
        Converts this OllamaStreamResponse object to a normalized LLMStreamResponse object.
        
        Returns:
            LLMStreamResponse:
                A normalized representation of a LLM provider API response.
            
        Raises:
            pydantic.ValidationError:
                If any discrepancies are found in the model.
        """
        
        token_count = None
        if self.prompt_eval_count and self.eval_count:
            token_count = self.prompt_eval_count + self.eval_count

        return LLMStreamResponse(
            model=self.model,
            created_at=self.created_at,
            response=self.response,
            done=self.done,
            total_duration=self.total_duration,
            token_count=token_count
        )
        