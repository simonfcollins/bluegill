import httpx
import json
from typing import AsyncGenerator
from pydantic import ValidationError
from datetime import datetime, UTC

from bluegill_shared.models import Message

from bluegill_agent.providers.base import BaseLLMProvider
from bluegill_agent.providers.ollama.models import OllamaStreamResponse
from bluegill_agent.schemas import LLMStreamResponse
from bluegill_agent.exceptions.provider_exception import ProviderError


class LocalOllamaProvider(BaseLLMProvider):
    """
    Implementation of BaseLLMProvider using the Ollama API.
    """
    
    NAME: str = "ollama"
    
    
    def __init__(self, base_url: str = "http://127.0.0.1:11434") -> None:
        self.base_url = base_url.rstrip("/")

    
    async def generate(self, 
        model: str,
        messages: list[Message], 
        window: int = 8000
    ) -> LLMStreamResponse:
        async with httpx.AsyncClient() as client:     
            try:       
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": self.format_messages(messages),
                        "stream": False,
                        "think": False,
                        "options": {"num_ctx": window}
                    },
                    timeout=httpx.Timeout(None, read=300)
                )
            except httpx.ConnectError as e:
                raise ProviderError(f"could not reach ollama at '{self.base_url}': {e}")
                
            response.raise_for_status()
            
            try:    
                return OllamaStreamResponse.model_validate_json(response.text).to_llm_stream_response()
            except ValidationError:
                return LLMStreamResponse(
                    model=model,
                    done=True,
                    created_at=datetime.now(UTC).isoformat(),
                    response=f"Unexpected response from provider: '{response.text}'"
                )
        
        
    async def stream(self,
        model: str,
        messages: list[Message],
        system_prompt: str,
        window: int = 8000
    ) -> AsyncGenerator[LLMStreamResponse, None]:
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": self.format_messages(messages),
                        "stream": True,
                        "think": False,
                        "system": system_prompt,
                        "options": {"num_ctx": window}
                    },
                    timeout=httpx.Timeout(None, read=300)
                ) as raw_response:

                    raw_response.raise_for_status()

                    async for line in raw_response.aiter_lines():
                        if not line.strip():
                            continue

                        try:
                            yield OllamaStreamResponse.model_validate_json(line).to_llm_stream_response()
                        except ValidationError:
                            yield LLMStreamResponse(
                                model=model,
                                created_at=datetime.now(UTC).isoformat(),
                                response=f"unexpected response from provider: '{line}'"
                            )

            except httpx.ConnectError as e:
                raise ProviderError(f"could not reach ollama at '{self.base_url}': {e}")
                        
    
    async def model_exists(self, model: str) -> bool:
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                response = await client.get(f"{self.base_url}/api/tags")
            except httpx.ConnectError as e:
                raise ProviderError(f"could not reach ollama at '{self.base_url}': {e}")
            
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError:
                raise ProviderError(f"ollama responded with status code {e.status_code}: '{e.detail}'")
            
            try:
                data = response.json()
            except ValueError:
                raise ProviderError("invalid JSON response from provider")
            
            models = data.get("models", [])
            
            return any(m.get("name") == model for m in models)
