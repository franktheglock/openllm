"""
OpenRouter LLM provider implementation.
"""
import os
from typing import List, Dict, Any, Optional, AsyncIterator, Union
import aiohttp
import asyncio

from .openai_provider import OpenAIProvider
from .base import BaseLLMProvider, Message, LLMResponse
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class OpenRouterProvider(OpenAIProvider):
    """
    OpenRouter API provider.
    Uses OpenAI-compatible API but with different base URL.
    """
    
    _cached_models = None  # Cache for model list
    _cached_model_info = {}  # Cache for model details (context windows, pricing)
    _cache_timestamp = 0
    _cache_ttl = 3600  # Cache for 1 hour
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize OpenRouter provider."""
        api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OpenRouter API key not provided")
        
        # Use OpenAI client but with OpenRouter base URL
        super().__init__(api_key, **kwargs)
        # Override the base URL
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        logger.info("OpenRouter provider initialized")
    
    async def complete(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Union[int, str] = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Get completion from OpenRouter, with auto context window support."""
        # Handle 'auto' max_tokens by looking up model's context window
        resolved_max_tokens = max_tokens
        if isinstance(max_tokens, str) and max_tokens.lower() == 'auto':
            resolved_max_tokens = self.get_model_context_window(model)
            logger.info(f"Auto max_tokens for {model}: using {resolved_max_tokens}")
        
        # Add a unique request ID to bypass prompt caching
        import uuid
        request_id = str(uuid.uuid4())
        
        # Disable prompt caching on OpenRouter to prevent returning cached responses
        kwargs['extra_headers'] = {
            'X-Request-ID': request_id,
            'Cache-Control': 'no-cache, no-store, must-revalidate'
        }
        
        # Call parent's complete method with resolved max_tokens
        return await super().complete(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=resolved_max_tokens,
            tools=tools,
            **kwargs
        )
    
    async def stream_complete(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Union[int, str] = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion from OpenRouter, with auto context window support."""
        # Handle 'auto' max_tokens by looking up model's context window
        resolved_max_tokens = max_tokens
        if isinstance(max_tokens, str) and max_tokens.lower() == 'auto':
            resolved_max_tokens = self.get_model_context_window(model)
            logger.info(f"Auto max_tokens for {model}: using {resolved_max_tokens}")
        
        # Call parent's stream_complete method with resolved max_tokens
        async for chunk in super().stream_complete(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=resolved_max_tokens,
            tools=tools,
            **kwargs
        ):
            yield chunk
    
    async def fetch_models_from_api(self) -> List[str]:
        """Fetch available models from OpenRouter API."""
        try:
            import time
            
            # Check cache
            if (self._cached_models and 
                time.time() - self._cache_timestamp < self._cache_ttl):
                return self._cached_models
            
            async with aiohttp.ClientSession() as session:
                async with session.get('https://openrouter.ai/api/v1/models') as response:
                    if response.status == 200:
                        data = await response.json()
                        # Extract model IDs and store full info
                        models = []
                        for model in data.get('data', []):
                            model_id = model['id']
                            models.append(model_id)
                            # Store context window and pricing info
                            self._cached_model_info[model_id] = {
                                'context_length': model.get('context_length', 4096),
                                'pricing': model.get('pricing', {}),
                                'name': model.get('name', model_id)
                            }
                        
                        # Cache the results
                        self._cached_models = models
                        self._cache_timestamp = time.time()
                        
                        logger.info(f"Fetched {len(models)} models from OpenRouter API")
                        return models
                    else:
                        logger.warning(f"Failed to fetch OpenRouter models: {response.status}")
                        return self._get_default_models()
        except Exception as e:
            logger.error(f"Error fetching OpenRouter models: {e}")
            return self._get_default_models()
    
    def _get_default_models(self) -> List[str]:
        """Get default/fallback model list."""
        return [
            'openai/gpt-4o',
            'openai/gpt-4-turbo',
            'openai/gpt-3.5-turbo',
            'anthropic/claude-3-5-sonnet-20241022',
            'anthropic/claude-3-opus-20240229',
            'anthropic/claude-3-haiku-20240307',
            'google/gemini-pro-1.5',
            'google/gemini-flash-1.5',
            'meta-llama/llama-3.2-90b-vision-instruct',
            'mistralai/mixtral-8x22b-instruct'
        ]
    
    def get_available_models(self) -> List[str]:
        """
        Get available OpenRouter models.
        Returns cached list or default list (use fetch_models_from_api for fresh data).
        """
        if self._cached_models:
            return self._cached_models
        return self._get_default_models()
    
    def get_model_context_window(self, model_id: str) -> int:
        """
        Get the context window (max tokens) for a specific model.
        
        Args:
            model_id: The model ID (e.g., 'openai/gpt-4o')
            
        Returns:
            The context window size in tokens
        """
        # Check cached model info
        if model_id in self._cached_model_info:
            context_length = self._cached_model_info[model_id]['context_length']
            logger.info(f"Auto-detected context window for {model_id}: {context_length}")
            return context_length
        
        # Default context windows for common models if not cached
        default_windows = {
            'openai/gpt-4o': 128000,
            'openai/gpt-4-turbo': 128000,
            'openai/gpt-3.5-turbo': 16385,
            'anthropic/claude-3-5-sonnet-20241022': 200000,
            'anthropic/claude-3-opus-20240229': 200000,
            'anthropic/claude-3-haiku-20240307': 200000,
            'google/gemini-pro-1.5': 1000000,
            'google/gemini-flash-1.5': 1000000,
            'meta-llama/llama-3.2-90b-vision-instruct': 128000,
            'mistralai/mixtral-8x22b-instruct': 64000
        }
        
        if model_id in default_windows:
            logger.info(f"Using default context window for {model_id}: {default_windows[model_id]}")
            return default_windows[model_id]
        
        # Conservative default if unknown
        logger.warning(f"Unknown model {model_id}, using conservative context window of 4096")
        return 4096
    
    def estimate_cost(self, usage: Dict[str, int], model: str) -> float:
        """
        Estimate cost for OpenRouter.
        Note: OpenRouter pricing varies by model. This is a rough estimate.
        """
        # Simplified pricing - actual pricing varies
        base_cost_per_1k = 0.002  # Average estimate
        total_tokens = usage.get('total_tokens', 0)
        return (total_tokens / 1000) * base_cost_per_1k
