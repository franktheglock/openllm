"""
OpenAI LLM provider implementation.
"""
import os
from typing import List, Dict, Any, Optional, AsyncIterator
import openai
from openai import AsyncOpenAI

from .base import BaseLLMProvider, Message, LLMResponse
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider."""
    
    # Pricing per 1K tokens (as of 2024)
    PRICING = {
        'gpt-4-turbo-preview': {'input': 0.01, 'output': 0.03},
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-4-32k': {'input': 0.06, 'output': 0.12},
        'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
        'gpt-3.5-turbo-16k': {'input': 0.001, 'output': 0.002},
    }
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize OpenAI provider."""
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not provided")
        
        super().__init__(api_key, **kwargs)
        self.client = AsyncOpenAI(api_key=api_key)
        logger.info("OpenAI provider initialized")
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert internal Message format to OpenAI format."""
        converted = []
        for msg in messages:
            openai_msg = {
                'role': msg.role,
                'content': msg.content
            }
            if msg.name:
                openai_msg['name'] = msg.name
            if msg.tool_calls:
                openai_msg['tool_calls'] = msg.tool_calls
            if msg.tool_call_id:
                openai_msg['tool_call_id'] = msg.tool_call_id
            
            converted.append(openai_msg)
        
        return converted
    
    async def complete(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Get completion from OpenAI."""
        try:
            # Add a unique request ID to bypass any caching
            import uuid
            request_id = str(uuid.uuid4())
            
            params = {
                'model': model,
                'messages': self._convert_messages(messages),
                'temperature': temperature,
                'max_tokens': max_tokens,
                **kwargs
            }
            
            if tools:
                params['tools'] = tools
            
            # Include unique request ID in extra headers to prevent caching
            params['extra_headers'] = {
                'X-Request-ID': request_id
            }
            
            response = await self.client.chat.completions.create(**params)
            
            choice = response.choices[0]
            
            # Convert tool_calls to dict format if present
            tool_calls = None
            if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                tool_calls = [
                    {
                        'id': tc.id,
                        'type': tc.type,
                        'function': {
                            'name': tc.function.name,
                            'arguments': tc.function.arguments
                        }
                    }
                    for tc in choice.message.tool_calls
                ]
            
            return LLMResponse(
                content=choice.message.content or "",
                model=response.model,
                usage={
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason
            )
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def stream_complete(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion from OpenAI."""
        try:
            params = {
                'model': model,
                'messages': self._convert_messages(messages),
                'temperature': temperature,
                'max_tokens': max_tokens,
                'stream': True,
                **kwargs
            }
            
            if tools:
                params['tools'] = tools
            
            stream = await self.client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available OpenAI models."""
        return [
            'gpt-4-turbo-preview',
            'gpt-4',
            'gpt-4-32k',
            'gpt-3.5-turbo',
            'gpt-3.5-turbo-16k'
        ]
    
    def estimate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Estimate cost for OpenAI request."""
        if model not in self.PRICING:
            # Use GPT-4 pricing as fallback
            model = 'gpt-4'
        
        pricing = self.PRICING[model]
        input_cost = (usage.get('prompt_tokens', 0) / 1000) * pricing['input']
        output_cost = (usage.get('completion_tokens', 0) / 1000) * pricing['output']
        
        return input_cost + output_cost
