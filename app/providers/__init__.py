"""Provider registry for dynamic provider management."""

from typing import Dict, List

from app.providers.base import ProviderInterface


class ProviderRegistry:
    """Registry for managing DDL providers."""

    _providers: Dict[str, ProviderInterface] = {}

    @classmethod
    def register(cls, provider: ProviderInterface) -> None:
        """Register a provider instance."""
        cls._providers[provider.name] = provider

    @classmethod
    def get(cls, name: str) -> ProviderInterface | None:
        """Get a provider by name."""
        return cls._providers.get(name)

    @classmethod
    def all(cls) -> List[ProviderInterface]:
        """Get all registered providers."""
        return list(cls._providers.values())

    @classmethod
    def names(cls) -> List[str]:
        """Get names of all registered providers."""
        return list(cls._providers.keys())


# Convenience function for registration
def register_provider(provider: ProviderInterface) -> None:
    """Register a provider with the global registry."""
    ProviderRegistry.register(provider)
