# Up to date as of Ollama version 0.30.11

import httpx
from typing import AsyncGenerator
from pydantic import ValidationError
from datetime import datetime, UTC

from bluegill_shared.models import Message

from bluegill_agent.providers.base import BaseLLMProvider
from bluegill_agent.providers.ollama.models import OllamaStreamResponse, OllamaTag
from bluegill_agent.schemas import LLMStreamResponse
from bluegill_agent.exceptions.provider_exception import ProviderError, AbilityError


class LocalOllamaProvider(BaseLLMProvider):
    """
    Implementation of BaseLLMProvider using the Ollama API.
    """
    
    NAME: str = "ollama"
    
    
    def __init__(self, base_url: str = "http://127.0.0.1:11434") -> None:
        super().__init__(base_url=base_url)

    
    async def generate(
        self, 
        model: str,
        messages: list[Message], 
        window: int = 8000
    ) -> LLMStreamResponse:
        try:       
            response = await self._client.post(
                "/api/generate",
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
            raise ProviderError(f"Could not reach ollama at '{self.base_url}'") from e
        
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"Ollama responded with status code '{e.response.status_code}") from e
            
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
        
        
    async def stream(
        self,
        model: str,
        messages: list[Message],
        system_prompt: str,
        window: int = 8000,
        think: bool = False
    ) -> AsyncGenerator[LLMStreamResponse, None]:
        capabilities = ["tools", "completion"]

        if think:
            capabilities.append("thinking")
        
        missing_capabilities = await self._verify_capabilities(model, capabilities)
        missing = ", ".join(missing_capabilities)
        
        if missing_capabilities:
            raise AbilityError(f"Model '{model}' does not support '{missing}'")
        
        try:
            async with self._client.stream(
                "POST",
                "/api/generate",
                json={
                    "model": model,
                    "prompt": self.format_messages(messages),
                    "stream": True,
                    "think": think,
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
                            response=f"Unexpected response from provider: '{line}'"
                        )
                        
        except httpx.ConnectError as e:
            raise ProviderError(f"Could not reach ollama at '{self.base_url}'") from e
        
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"Ollama responded with status code '{e.response.status_code}") from e
                        
    
    async def model_exists(self, model: str) -> bool:     
        return any(m.name == model for m in await self._tags())
        
        
    async def _tags(self) -> list[OllamaTag]:
        """
        Retrieves a list of downloaded models from Ollama.
        """
        
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()

            data = response.json()
            tags = data.get("models", [])
            
            return [OllamaTag.model_validate(t) for t in tags]

        except httpx.ConnectError as e:
            raise ProviderError(f"Could not reach ollama at '{self.base_url}'") from e
        
        except httpx.HTTPStatusError as e:
                raise ProviderError(f"Ollama responded with status code {e.response.status_code}: '{e.response.text}'") from e
            
        except ValidationError as e:
            raise ProviderError("Error validating response from ollama") from e
            
        except ValueError as e:
            raise ProviderError("Invalid JSON response from ollama") from e
        
            
    async def _verify_capabilities(self, model: str, capabilities: list[str]) -> list[str]:
        """
        Returns the capabilities from `capabilities` that `model` does not support.
        If the model does not exist, all requested capabilities are considered missing.
        """

        tags = await self._tags()
        tag = next((t for t in tags if t.name == model), None)

        if tag is None or tag.capabilities is None:
            return capabilities
        
        available = set(tag.capabilities)

        return [c for c in capabilities if c not in available]