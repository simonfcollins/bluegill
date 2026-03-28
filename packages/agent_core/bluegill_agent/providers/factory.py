from bluegill_agent.providers.openai_provider import OpenAIProvider
from bluegill_agent.providers.anthropic_provider import AnthropicProvider
from bluegill_agent.providers.local_ollama_provider import LocalOllamaProvider

class ProviderFactory:
    _providers = {
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
        "ollama": LocalOllamaProvider(),
    }

    @classmethod
    def get_provider(cls, provider_name: str):
        provider = cls._providers.get(provider_name.lower())
        if not provider:
            raise ValueError(f"Unsupported provider: {provider_name}")
        return provider