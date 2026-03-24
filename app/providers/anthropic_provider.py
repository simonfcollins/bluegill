from app.providers.base import BaseLLMProvider

class AnthropicProvider(BaseLLMProvider):
    async def generate(self, messages: list[dict], model: str) -> str:
        raise NotImplementedError