from pydantic import BaseModel

class LLMRequest(BaseModel):
    provider: str
    model: str
    prompt: str

class LLMResponse(BaseModel):
    response: str