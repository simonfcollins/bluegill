from bluegill_agent.providers.base import BaseLLMProvider
from bluegill_agent.providers.ollama.provider import LocalOllamaProvider
from bluegill_agent.exceptions.provider_exception import InvalidProviderError


class ProviderFactory:
    _providers = {
        "ollama": LocalOllamaProvider,
    }

    @classmethod
    def create(cls, provider_name: str, base_url: str) -> BaseLLMProvider:
        """
        A factory method to retrieve a provider object by common provider name.
        """
        
        provider = cls._providers.get(provider_name.lower())
        
        if not provider:
            raise InvalidProviderError(f"Unsupported provider: {provider_name}")
        
        return provider(base_url=base_url)
