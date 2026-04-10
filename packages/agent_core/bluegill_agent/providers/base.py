from abc import ABC, abstractmethod
from typing import AsyncGenerator

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: list[dict], model: str) -> str:
        raise NotImplementedError

    async def stream(self, messages: list[dict], model: str) -> AsyncGenerator[str, None]:
        raise NotImplementedError
