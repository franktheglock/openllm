"""
LLM provider factory and manager.
"""
import os
from typing import Dict, Type, Optional
from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .ollama_provider import OllamaProvider
from .openrouter_provider import OpenRouterProvider
from .gemini_provider import GeminiProvider
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""
    
    _providers: Dict[str, Type[BaseLLMProvider]] = {
        'gemini': GeminiProvider,
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'ollama': OllamaProvider,
        'openrouter': OpenRouterProvider,
    }
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseLLMProvider]):
        """
        Register a new LLM provider.
        
        Args:
            name: Provider name
            provider_class: Provider class
        """
        cls._providers[name] = provider_class
        logger.info(f"Registered LLM provider: {name}")
    
    @classmethod
    def create_provider(
        cls,
        provider_name: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider_name: Name of the provider
            api_key: API key (optional, will use environment variable if not provided)
            **kwargs: Additional provider-specific parameters
        
        Returns:
            Provider instance
        
        Raises:
            ValueError: If provider is not registered
        """
        if provider_name not in cls._providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider_class = cls._providers[provider_name]
        
        try:
            return provider_class(api_key=api_key, **kwargs)
        except Exception as e:
            logger.error(f"Failed to create provider {provider_name}: {e}")
            raise
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of registered provider names."""
        return list(cls._providers.keys())
