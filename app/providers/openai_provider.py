from app.providers.base import BaseLLMProvider

class OpenAIProvider(BaseLLMProvider):
    async def generate(self, messages: list[dict], model: str) -> str:
        raise NotImplementedError