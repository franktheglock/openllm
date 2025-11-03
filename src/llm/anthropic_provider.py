"""
Anthropic (Claude) LLM provider implementation.
"""
import os
from typing import List, Dict, Any, Optional, AsyncIterator
from anthropic import AsyncAnthropic

from .base import BaseLLMProvider, Message, LLMResponse
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider."""
    
    # Pricing per 1M tokens
    PRICING = {
        'claude-3-opus-20240229': {'input': 15.0, 'output': 75.0},
        'claude-3-sonnet-20240229': {'input': 3.0, 'output': 15.0},
        'claude-3-haiku-20240307': {'input': 0.25, 'output': 1.25},
    }
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize Anthropic provider."""
        api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("Anthropic API key not provided")
        
        super().__init__(api_key, **kwargs)
        self.client = AsyncAnthropic(api_key=api_key)
        logger.info("Anthropic provider initialized")
    
    def _convert_messages(self, messages: List[Message]) -> tuple[str, List[Dict[str, Any]]]:
        """
        Convert internal Message format to Anthropic format.
        Returns (system_prompt, messages_list)
        """
        system_prompt = ""
        converted = []
        
        for msg in messages:
            if msg.role == 'system':
                system_prompt = msg.content
            else:
                converted.append({
                    'role': msg.role if msg.role != 'tool' else 'user',
                    'content': msg.content
                })
        
        return system_prompt, converted
    
    async def complete(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Get completion from Anthropic."""
        try:
            system_prompt, anthropic_messages = self._convert_messages(messages)
            
            params = {
                'model': model,
                'messages': anthropic_messages,
                'max_tokens': max_tokens,
                'temperature': temperature,
                **kwargs
            }
            
            if system_prompt:
                params['system'] = system_prompt
            
            if tools:
                # Convert to Anthropic tool format
                params['tools'] = [self._convert_tool(t) for t in tools]
            
            response = await self.client.messages.create(**params)
            
            content = ""
            if response.content:
                content = " ".join([
                    block.text for block in response.content 
                    if hasattr(block, 'text')
                ])
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage={
                    'prompt_tokens': response.usage.input_tokens,
                    'completion_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                },
                finish_reason=response.stop_reason
            )
        
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
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
        """Stream completion from Anthropic."""
        try:
            system_prompt, anthropic_messages = self._convert_messages(messages)
            
            params = {
                'model': model,
                'messages': anthropic_messages,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'stream': True,
                **kwargs
            }
            
            if system_prompt:
                params['system'] = system_prompt
            
            if tools:
                params['tools'] = [self._convert_tool(t) for t in tools]
            
            async with self.client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text
        
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise
    
    def _convert_tool(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAI-style tool to Anthropic format."""
        return {
            'name': tool['function']['name'],
            'description': tool['function']['description'],
            'input_schema': tool['function']['parameters']
        }
    
    def get_available_models(self) -> List[str]:
        """Get available Anthropic models."""
        return [
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307'
        ]
    
    def estimate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Estimate cost for Anthropic request."""
        if model not in self.PRICING:
            # Use Opus pricing as fallback
            model = 'claude-3-opus-20240229'
        
        pricing = self.PRICING[model]
        input_cost = (usage.get('prompt_tokens', 0) / 1_000_000) * pricing['input']
        output_cost = (usage.get('completion_tokens', 0) / 1_000_000) * pricing['output']
        
        return input_cost + output_cost
