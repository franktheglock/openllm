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
            elif msg.role == 'tool':
                # Represent tool outputs as tool messages so Gemini sees the results
                # and can incorporate them into the next reply. Prefix content if not already prefixed.
                content = msg.content or ''
                chat_history.append({
                    'role': 'tool',
                    'parts': [content]
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
            
            # If tools are provided, inject a brief machine-readable description into the system instruction
            # so Gemini knows about available tools and how to request them. We keep this short to avoid
            # overwhelming the model but include an explicit JSON-call format hint which we parse below.
            system_instr = system_instruction or ""
            if tools:
                try:
                    import json
                    tools_desc = json.dumps([{ 'name': t.get('name') or t.get('id') or t.get('function', {}).get('name'), 'description': t.get('description', ''), 'parameters': t.get('parameters', {}) } for t in tools])
                    system_instr += (
                        "\n\nAvailable tools (JSON): " + tools_desc +
                        "\nIf you want to call a tool, output ONLY a single JSON object containing a 'function' key with 'name' and 'arguments' fields, for example:\n"
                        "{\"function\": {\"name\": \"web_search\", \"arguments\": {\"query\": \"latest AI news\"}}}\n"
                    )
                except Exception:
                    # fall back silently if tools can't be serialized
                    pass

            model_instance = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                system_instruction=system_instr if system_instr else None
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
            except Exception:
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0

            # Normalize content
            content = getattr(response, 'text', None)
            if not content:
                # Try common alternative locations
                candidates = getattr(response, 'candidates', None)
                if candidates and len(candidates) > 0:
                    # candidate may have 'content' or 'text'
                    c = candidates[0]
                    content = getattr(c, 'content', None) or getattr(c, 'text', None) or ''
                else:
                    content = ''

            # Try to extract tool_calls from several possible response shapes.
            tool_calls = None

            # 1) Native field on response (if present)
            if hasattr(response, 'tool_calls') and getattr(response, 'tool_calls'):
                tool_calls = []
                for tc in response.tool_calls:
                    try:
                        fn = getattr(tc, 'function', None)
                        if fn is not None:
                            tool_calls.append({
                                'id': getattr(tc, 'id', None),
                                'type': getattr(tc, 'type', None),
                                'function': {
                                    'name': getattr(fn, 'name', None),
                                    'arguments': getattr(fn, 'arguments', None)
                                }
                            })
                        else:
                            # Fallback dict-like
                            tool_calls.append(dict(tc))
                    except Exception:
                        continue

            # 2) Candidates may include tool_calls
            if not tool_calls:
                candidates = getattr(response, 'candidates', None)
                if candidates:
                    for c in candidates:
                        tc_attr = getattr(c, 'tool_calls', None) or (getattr(c, 'message', None) and getattr(c.message, 'tool_calls', None))
                        if tc_attr:
                            tool_calls = []
                            for tc in tc_attr:
                                try:
                                    fn = getattr(tc, 'function', None)
                                    if fn is not None:
                                        tool_calls.append({
                                            'id': getattr(tc, 'id', None),
                                            'type': getattr(tc, 'type', None),
                                            'function': {
                                                'name': getattr(fn, 'name', None),
                                                'arguments': getattr(fn, 'arguments', None)
                                            }
                                        })
                                    else:
                                        tool_calls.append(dict(tc))
                                except Exception:
                                    continue
                            break

            # 3) As a last resort try to parse JSON embedded in the text (models sometimes emit a JSON tool call)
            if not tool_calls and content:
                import json
                try:
                    # Find first JSON object in the text
                    start = content.find('{')
                    end = content.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        maybe_json = content[start:end+1]
                        parsed = json.loads(maybe_json)
                        # Heuristics: look for either 'function' or 'tool' keys
                        if isinstance(parsed, dict) and ('function' in parsed or 'tool' in parsed or 'name' in parsed):
                            # Normalize into tool_calls structure
                            fn_obj = parsed.get('function') or {'name': parsed.get('tool') or parsed.get('name'), 'arguments': parsed.get('arguments') or parsed.get('args')}
                            tool_calls = [{
                                'id': parsed.get('id'),
                                'type': parsed.get('type'),
                                'function': fn_obj
                            }]
                except Exception:
                    # ignore JSON parse errors
                    pass

            return LLMResponse(
                content=content,
                model=model,
                usage={
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': total_tokens
                },
                tool_calls=tool_calls,
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
