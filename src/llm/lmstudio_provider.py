"""
LM Studio provider implementation.
"""
import os
import aiohttp
from typing import List, Dict, Optional
from .base import BaseLLMProvider, Message, LLMResponse


class LMStudioProvider(BaseLLMProvider):
    """LM Studio local server provider."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize LM Studio provider.
        
        Args:
            api_key: Not used for LM Studio
            base_url: LM Studio server URL (default: http://localhost:1234/v1)
        """
        self.base_url = base_url or os.getenv('LMSTUDIO_BASE_URL', 'http://localhost:1234/v1')
        self.api_key = api_key or 'not-needed'  # LM Studio doesn't require API key
    
    async def complete(
        self,
        messages: List[Message],
        model: str = "local-model",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict]] = None
    ) -> LLMResponse:
        """
        Get completion from LM Studio.
        
        Args:
            messages: Conversation messages
            model: Model identifier (LM Studio uses loaded model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Tool definitions (not supported by LM Studio)
        
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
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{self.base_url}/chat/completions',
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"LM Studio API error: {error_text}")
                
                data = await response.json()
                
                choice = data['choices'][0]
                content = choice['message']['content']
                finish_reason = choice.get('finish_reason', 'stop')
                
                usage = data.get('usage', {})
                
                return LLMResponse(
                    content=content,
                    finish_reason=finish_reason,
                    usage={
                        'prompt_tokens': usage.get('prompt_tokens', 0),
                        'completion_tokens': usage.get('completion_tokens', 0),
                        'total_tokens': usage.get('total_tokens', 0)
                    }
                )
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        # LM Studio uses whatever model is loaded
        return ['local-model', 'lmstudio']
    
    def estimate_cost(self, usage: Dict, model: str) -> float:
        """Estimate cost (LM Studio is free)."""
        return 0.0
