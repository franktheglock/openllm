"""
Google Gemini LLM provider implementation.
"""
import os
from typing import List, Dict, Any, Optional, AsyncIterator
import google.generativeai as genai
import asyncio

from .base import BaseLLMProvider, Message, LLMResponse
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider."""
    
    # Pricing per 1M tokens (as of 2024)
    PRICING = {
        'gemini-pro': {'input': 0.5, 'output': 1.5},
        'gemini-pro-vision': {'input': 0.5, 'output': 1.5},
        'gemini-1.5-pro': {'input': 3.5, 'output': 10.5},
        'gemini-1.5-flash': {'input': 0.35, 'output': 1.05},
    }
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize Gemini provider."""
        api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("Gemini API key not provided")
        
        super().__init__(api_key, **kwargs)
        genai.configure(api_key=api_key)
        logger.info("Gemini provider initialized")
    
    def _convert_messages(self, messages: List[Message]) -> tuple[str, List[Dict[str, str]]]:
        """
        Convert internal Message format to Gemini format.
        Returns (system_instruction, chat_history)
        """
        system_instruction = ""
        chat_history = []
        
        for msg in messages:
            if msg.role == 'system':
                system_instruction = msg.content
            elif msg.role == 'user':
                chat_history.append({
                    'role': 'user',
                    'parts': [msg.content]
                })
            elif msg.role == 'assistant':
                chat_history.append({
                    'role': 'model',
                    'parts': [msg.content]
                })
        
        return system_instruction, chat_history
    
    async def complete(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Get completion from Gemini."""
        try:
            system_instruction, chat_history = self._convert_messages(messages)
            
            # Create model
            generation_config = {
                'temperature': temperature,
                'max_output_tokens': max_tokens,
            }
            
            model_instance = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                system_instruction=system_instruction if system_instruction else None
            )
            
            # Start chat or single message
            if len(chat_history) > 1:
                chat = model_instance.start_chat(history=chat_history[:-1])
                response = await asyncio.to_thread(
                    chat.send_message,
                    chat_history[-1]['parts'][0]
                )
            else:
                prompt = chat_history[0]['parts'][0] if chat_history else ""
                response = await asyncio.to_thread(
                    model_instance.generate_content,
                    prompt
                )
            
            # Extract usage info
            try:
                prompt_tokens = response.usage_metadata.prompt_token_count
                completion_tokens = response.usage_metadata.candidates_token_count
                total_tokens = response.usage_metadata.total_token_count
            except:
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0
            
            return LLMResponse(
                content=response.text,
                model=model,
                usage={
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': total_tokens
                },
                finish_reason='stop'
            )
        
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
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
        """Stream completion from Gemini."""
        try:
            system_instruction, chat_history = self._convert_messages(messages)
            
            generation_config = {
                'temperature': temperature,
                'max_output_tokens': max_tokens,
            }
            
            model_instance = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                system_instruction=system_instruction if system_instruction else None
            )
            
            if len(chat_history) > 1:
                chat = model_instance.start_chat(history=chat_history[:-1])
                response = await asyncio.to_thread(
                    chat.send_message,
                    chat_history[-1]['parts'][0],
                    stream=True
                )
            else:
                prompt = chat_history[0]['parts'][0] if chat_history else ""
                response = await asyncio.to_thread(
                    model_instance.generate_content,
                    prompt,
                    stream=True
                )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get available Gemini models."""
        return [
            'gemini-1.5-flash',  # Recommended - fast and cheap
            'gemini-1.5-pro',
            'gemini-pro',
        ]
    
    def estimate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Estimate cost for Gemini request."""
        # Default to gemini-1.5-flash if model not in pricing
        if model not in self.PRICING:
            model = 'gemini-1.5-flash'
        
        pricing = self.PRICING.get(model, self.PRICING['gemini-1.5-flash'])
        input_cost = (usage.get('prompt_tokens', 0) / 1_000_000) * pricing['input']
        output_cost = (usage.get('completion_tokens', 0) / 1_000_000) * pricing['output']
        
        return input_cost + output_cost
