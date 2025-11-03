"""
Base LLM provider interface.
All LLM providers must implement this interface for uniform usage.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass


@dataclass
class Message:
    """Represents a chat message."""
    role: str  # 'system', 'user', 'assistant', 'tool'
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


@dataclass
class LLMResponse:
    """Response from an LLM."""
    content: str
    model: str
    usage: Dict[str, int]  # tokens used
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: str = "stop"


class BaseLLMProvider(ABC):
    """Base class for all LLM providers."""
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize the LLM provider.
        
        Args:
            api_key: API key for the provider
            **kwargs: Additional provider-specific parameters
        """
        self.api_key = api_key
        self.kwargs = kwargs
    
    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Get a completion from the LLM.
        
        Args:
            messages: List of messages in the conversation
            model: Model identifier
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens to generate
            tools: Available tools for function calling
            **kwargs: Additional provider-specific parameters
        
        Returns:
            LLMResponse object
        """
        pass
    
    @abstractmethod
    async def stream_complete(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream a completion from the LLM.
        
        Args:
            messages: List of messages in the conversation
            model: Model identifier
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens to generate
            tools: Available tools for function calling
            **kwargs: Additional provider-specific parameters
        
        Yields:
            Chunks of the response text
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for this provider.
        
        Returns:
            List of model identifiers
        """
        pass
    
    def estimate_cost(self, usage: Dict[str, int], model: str) -> float:
        """
        Estimate the cost of a request in USD.
        
        Args:
            usage: Token usage dictionary
            model: Model identifier
        
        Returns:
            Estimated cost in USD
        """
        # Override in subclasses with actual pricing
        return 0.0
