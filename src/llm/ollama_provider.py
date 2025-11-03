"""
Ollama LLM provider implementation (local models).
"""
import os
import json
from typing import List, Dict, Any, Optional, AsyncIterator
import aiohttp

from .base import BaseLLMProvider, Message, LLMResponse
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "http://localhost:11434", **kwargs):
        """Initialize Ollama provider."""
        super().__init__(api_key or "not-required", **kwargs)
        self.base_url = base_url.rstrip('/')
        logger.info(f"Ollama provider initialized (base_url: {self.base_url})")
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Convert internal Message format to Ollama format."""
        converted = []
        for msg in messages:
            converted.append({
                'role': msg.role,
                'content': msg.content
            })
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
        """Get completion from Ollama."""
        try:
            url = f"{self.base_url}/api/chat"
            
            payload = {
                'model': model,
                'messages': self._convert_messages(messages),
                'stream': False,
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    data = await response.json()
                    
                    return LLMResponse(
                        content=data.get('message', {}).get('content', ''),
                        model=model,
                        usage={
                            'prompt_tokens': data.get('prompt_eval_count', 0),
                            'completion_tokens': data.get('eval_count', 0),
                            'total_tokens': data.get('prompt_eval_count', 0) + data.get('eval_count', 0)
                        },
                        finish_reason='stop'
                    )
        
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
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
        """Stream completion from Ollama."""
        try:
            url = f"{self.base_url}/api/chat"
            
            payload = {
                'model': model,
                'messages': self._convert_messages(messages),
                'stream': True,
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    async for line in response.content:
                        if line:
                            data = json.loads(line)
                            if 'message' in data and 'content' in data['message']:
                                yield data['message']['content']
        
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available Ollama models."""
        # Common Ollama models
        return [
            'llama2',
            'llama2:13b',
            'llama2:70b',
            'mistral',
            'mixtral',
            'codellama',
            'phi',
            'neural-chat',
            'starling-lm'
        ]
    
    def estimate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Estimate cost for Ollama (free, local)."""
        return 0.0
