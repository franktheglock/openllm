"""
Custom OpenAI-compatible API endpoint provider.
"""
import os
import aiohttp
from typing import List, Dict, Optional
from .base import BaseLLMProvider, Message, LLMResponse


class CustomProvider(BaseLLMProvider):
    """Custom OpenAI-compatible API endpoint provider."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize Custom provider.
        
        Args:
            api_key: API key for the custom endpoint
            base_url: Custom API endpoint URL
        """
        self.api_key = api_key or os.getenv('CUSTOM_API_KEY', '')
        self.base_url = base_url or os.getenv('CUSTOM_BASE_URL', 'http://localhost:8000/v1')
    
    async def complete(
        self,
        messages: List[Message],
        model: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict]] = None
    ) -> LLMResponse:
        """
        Get completion from custom endpoint.
        
        Args:
            messages: Conversation messages
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Tool definitions (may not be supported)
        
        Returns:
            LLM response
        """
        # Convert messages to OpenAI format
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'role': msg.role,
                'content': msg.content
            })
        
        payload = {
            'model': model,
            'messages': formatted_messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        # Add tools if provided and supported
        if tools:
            payload['tools'] = tools
        
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{self.base_url}/chat/completions',
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Custom API error: {error_text}")
                
                data = await response.json()
                
                choice = data['choices'][0]
                content = choice['message'].get('content', '')
                finish_reason = choice.get('finish_reason', 'stop')
                
                # Handle tool calls if present
                tool_calls = None
                if 'tool_calls' in choice['message']:
                    tool_calls = choice['message']['tool_calls']
                
                usage = data.get('usage', {})
                
                return LLMResponse(
                    content=content,
                    finish_reason=finish_reason,
                    tool_calls=tool_calls,
                    usage={
                        'prompt_tokens': usage.get('prompt_tokens', 0),
                        'completion_tokens': usage.get('completion_tokens', 0),
                        'total_tokens': usage.get('total_tokens', 0)
                    }
                )
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        # Return common defaults, user can specify any model
        return ['default', 'custom-model']
    
    def estimate_cost(self, usage: Dict, model: str) -> float:
        """Estimate cost (depends on endpoint)."""
        # Cannot estimate without knowing the endpoint's pricing
        return 0.0
