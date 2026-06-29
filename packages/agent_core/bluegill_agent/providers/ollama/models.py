# Up to date as of Ollama version 0.30.11

from pydantic import BaseModel
from datetime import datetime

from bluegill_agent.schemas.llm_stream_response import LLMStreamResponse

class OllamaStreamResponse(BaseModel):
    """
    Respresents a single streamed chunk returned by the Ollama '/api/generate' endpoint
    when streaming is enabled.
    
    Attributes:
    
        model: Name of the model used to generate the response.
        
        created_at: The timestamp in UTC of when this chunk was created.
    
        response: The final generated response from the model.
                   
        thinking: The model's thinking if requested. 
                   
        done: True if this is the last chunk in the stream. False otherwise.
        
        context: An encoding of the conversation used in this response, 
                  this can be sent in the next request to keep a conversational memory.

        total_duration: Time spent generating the response.
        
        load_duration: Time spent in nanoseconds loading the model.
        
        prompt_eval_count: Number of tokens in the prompt.
        
        prompt_eval_duration: Time spent in nanoseconds evaluating the prompt.
        
        eval_count: Number of tokens in the response.
        
        eval_duration: Time in nanoseconds spent generating the response.
        
    Reference:
        https://ollama.readthedocs.io/en/api/#response
    """
    
    model: str
    created_at: str
    response: str = ""
    thinking: str | None = None
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
            thinking=self.thinking,
            done=self.done,
            total_duration=self.total_duration,
            token_count=token_count
        )
            
        
class OllamaTagDetails(BaseModel):
    """
    Represents specific details for an Ollama provided model.
    
    Attributes:

        format: Model file format (for example gguf).
        
        family: Primary model family (for example llama).
        
        families: All families the model belongs to, when applicable.
        
        parameter_size: Approximate parameter count label (for example 7B, 13B).
        
        quantization_level: Quantization level used (for example Q4_0).
        
        context_length: The maximum number of context units this model can injest.
        
    Reference:
        https://docs.ollama.com/api/tags
    """
    
    format: str | None = ""
    family: str | None = None
    families: list[str] | None = []
    parameter_size: str | None = None
    quantization_level: str | None = None
    context_length: int | None = None
    embedding_length: int | None = None
        
        
class OllamaTag(BaseModel):
    """
    Represents an object returned in response to the Ollama '/api/tags' endpoint.
    Contains information about a model.
    
    Attributes:
    
        name: Model name.
        
        model: Model name.
        
        remote_model: Name of the upstream model, if the model is remote.
        
        remote_host: URL of the upstream Ollama host, if the model is remote.
        
        modified_at: Last modified timestamp in ISO 8601 format.
        
        size: Total size of the model on disk in bytes.
        
        digest: SHA256 digest identifier of the model contents.
        
        details: Additional information about the model's format and family.
        
        capabilities: A list of capabilities supported by the model (for example 'thinking').

    Reference:
        https://docs.ollama.com/api/tags
    """
    
    name: str
    model: str
    remote_model: str | None = None
    remote_host: str | None = None
    modified_at: datetime
    size: int
    digest: str
    details: OllamaTagDetails
    capabilities: list[str] | None = None
    