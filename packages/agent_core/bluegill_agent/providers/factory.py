from bluegill_shared.utils import load_config

from bluegill_agent.providers.base import BaseLLMProvider
from bluegill_agent.providers.ollama.provider import LocalOllamaProvider
from bluegill_agent.exceptions.provider_exception import InvalidProviderError


config = load_config()


class ProviderFactory:
    _providers = {
        "ollama": LocalOllamaProvider,
    }

    @classmethod
    def get_provider(cls, provider_name: str) -> BaseLLMProvider:
        """
        A factory method to retrieve a provider object by common provider name.
        """
        
        provider = cls._providers.get(provider_name.lower())
        if not provider:
            raise InvalidProviderError(f"Unsupported provider: {provider_name}")
        
        for p in config.providers:
            if p.name == provider_name:
                return provider(p.url)
            
        return provider()
