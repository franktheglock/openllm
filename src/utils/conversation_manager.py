"""
Token-efficient conversation history management.
Handles intelligent pruning of message history to stay within token limits.
"""
import tiktoken
from typing import List, Dict, Any, Optional, Tuple
from src.llm.base import Message
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ConversationManager:
    """
    Manages conversation history with token-efficient pruning.
    
    Features:
    - Token counting using appropriate tokenizer for each model
    - Smart pruning that prioritizes recent and important messages
    - Reserves tokens for response generation
    - Handles system messages specially
    """
    
    # Default token limits (can be overridden in config)
    DEFAULT_MAX_TOKENS = 32000  # Conservative default
    DEFAULT_RESERVE_TOKENS = 2048  # Reserve for response generation
    DEFAULT_MIN_MESSAGES = 2  # Keep at least this many recent messages
    
    def __init__(self, 
                 max_context_tokens: int = DEFAULT_MAX_TOKENS,
                 reserve_tokens: int = DEFAULT_RESERVE_TOKENS,
                 min_messages: int = DEFAULT_MIN_MESSAGES):
        """
        Initialize conversation manager.
        
        Args:
            max_context_tokens: Maximum tokens to use for context
            reserve_tokens: Tokens to reserve for response generation
            min_messages: Minimum number of recent messages to keep
        """
        self.max_context_tokens = max_context_tokens
        self.reserve_tokens = reserve_tokens
        self.min_messages = min_messages
        
        # Cache tokenizers for different models
        self._tokenizers = {}
        
        logger.info(f"ConversationManager initialized: max_context={max_context_tokens}, reserve={reserve_tokens}")
    
    def _get_tokenizer(self, model: str) -> tiktoken.Encoding:
        """
        Get appropriate tokenizer for a model.
        
        Args:
            model: Model name/identifier
            
        Returns:
            tiktoken tokenizer
        """
        # Determine encoding based on model
        if model not in self._tokenizers:
            try:
                # Try model-specific encoding first
                if 'gpt-4' in model or 'gpt-3.5' in model:
                    encoding = tiktoken.encoding_for_model(model)
                elif 'claude' in model:
                    # Claude uses similar tokenization to GPT
                    encoding = tiktoken.get_encoding('cl100k_base')
                elif 'gemini' in model or 'palm' in model:
                    # Gemini uses similar tokenization
                    encoding = tiktoken.get_encoding('cl100k_base')
                else:
                    # Default to GPT-4 encoding for unknown models
                    encoding = tiktoken.get_encoding('cl100k_base')
                
                self._tokenizers[model] = encoding
                logger.debug(f"Cached tokenizer for model: {model}")
                
            except KeyError:
                # Fallback to cl100k_base (GPT-4) encoding
                encoding = tiktoken.get_encoding('cl100k_base')
                self._tokenizers[model] = encoding
                logger.warning(f"Unknown model {model}, using cl100k_base encoding")
        
        return self._tokenizers[model]
    
    def count_tokens(self, messages: List[Message], model: str) -> int:
        """
        Count total tokens in a list of messages.
        
        Args:
            messages: List of messages
            model: Model name for appropriate tokenization
            
        Returns:
            Total token count
        """
        if not messages:
            return 0
        
        tokenizer = self._get_tokenizer(model)
        total_tokens = 0
        
        for message in messages:
            # Count tokens in message content
            if message.content:
                total_tokens += len(tokenizer.encode(message.content))
            
            # Count tokens for tool calls (approximate)
            if message.tool_calls:
                # Tool calls add overhead - roughly estimate
                for tool_call in message.tool_calls:
                    # Function name + arguments + overhead
                    total_tokens += len(tokenizer.encode(str(tool_call))) + 10
            
            # Add tokens for message metadata (role, etc.)
            total_tokens += 4  # Rough estimate for message formatting
        
        return total_tokens
    
    def _calculate_message_priority(self, message: Message, index: int, total_messages: int) -> float:
        """
        Calculate priority score for a message (higher = more important to keep).
        
        Args:
            message: The message
            index: Position in conversation (0 = oldest)
            total_messages: Total messages in conversation
            
        Returns:
            Priority score (0-1, higher is better)
        """
        priority = 0.0
        
        # System messages get highest priority
        if message.role == 'system':
            priority += 1.0
        
        # Recent messages get higher priority
        recency_score = index / max(1, total_messages - 1)  # 0 to 1
        priority += recency_score * 0.8
        
        # Messages with tool calls get higher priority (contain important context)
        if message.tool_calls:
            priority += 0.3
        
        # Tool result messages get higher priority
        if message.role == 'tool':
            priority += 0.2
        
        # Longer messages might contain more context
        content_length = len(message.content) if message.content else 0
        if content_length > 100:
            priority += 0.1
        
        return min(1.0, priority)
    
    def prune_conversation(self, messages: List[Message], model: str) -> List[Message]:
        """
        Prune conversation history to fit within token limits.
        
        Args:
            messages: Full conversation history
            model: Model name for token counting
            
        Returns:
            Pruned conversation that fits within token limits
        """
        if not messages:
            return messages
        
        available_tokens = self.max_context_tokens - self.reserve_tokens
        
        # Always keep system message if present
        system_messages = [msg for msg in messages if msg.role == 'system']
        non_system_messages = [msg for msg in messages if msg.role != 'system']
        
        # If we have system messages, reserve space for them
        system_tokens = self.count_tokens(system_messages, model)
        available_tokens -= system_tokens
        
        if available_tokens <= 0:
            # Not enough space even for system messages - keep only essential
            logger.warning(f"System messages alone exceed token limit: {system_tokens} > {available_tokens + system_tokens}")
            return system_messages[:1] if system_messages else []
        
        # Calculate priorities for non-system messages
        message_priorities = []
        for i, msg in enumerate(non_system_messages):
            priority = self._calculate_message_priority(msg, i, len(non_system_messages))
            tokens = self.count_tokens([msg], model)
            message_priorities.append((priority, tokens, msg, i))
        
        # Sort by priority (highest first)
        message_priorities.sort(key=lambda x: x[0], reverse=True)
        
        # Greedily select messages that fit
        selected_messages = []
        total_tokens = 0
        
        for priority, tokens, msg, original_index in message_priorities:
            if total_tokens + tokens <= available_tokens:
                selected_messages.append((original_index, msg, tokens))
                total_tokens += tokens
            elif len(selected_messages) < self.min_messages:
                # Force keep minimum number of messages even if over limit
                selected_messages.append((original_index, msg, tokens))
                total_tokens += tokens
        
        # Sort back to original order
        selected_messages.sort(key=lambda x: x[0])
        pruned_messages = [msg for _, msg, _ in selected_messages]
        
        # Add back system messages at the beginning
        final_messages = system_messages + pruned_messages
        
        # Log pruning statistics
        original_tokens = self.count_tokens(messages, model)
        final_tokens = self.count_tokens(final_messages, model)
        
        if len(messages) != len(final_messages) or original_tokens != final_tokens:
            logger.info(f"Pruned conversation: {len(messages)}→{len(final_messages)} messages, "
                       f"{original_tokens}→{final_tokens} tokens ({available_tokens} available)")
        
        return final_messages
    
    def add_message(self, conversation: List[Message], message: Message, model: str) -> List[Message]:
        """
        Add a message to conversation and prune if necessary.
        
        Args:
            conversation: Current conversation history
            message: New message to add
            model: Model name for token counting
            
        Returns:
            Updated conversation (pruned if necessary)
        """
        new_conversation = conversation + [message]
        return self.prune_conversation(new_conversation, model)
    
    def get_conversation_stats(self, conversation: List[Message], model: str) -> Dict[str, Any]:
        """
        Get statistics about a conversation.
        
        Args:
            conversation: Conversation to analyze
            model: Model name for token counting
            
        Returns:
            Dictionary with conversation statistics
        """
        if not conversation:
            return {
                'total_messages': 0,
                'total_tokens': 0,
                'system_messages': 0,
                'user_messages': 0,
                'assistant_messages': 0,
                'tool_messages': 0,
                'avg_tokens_per_message': 0
            }
        
        tokens = self.count_tokens(conversation, model)
        
        role_counts = {}
        for msg in conversation:
            role_counts[msg.role] = role_counts.get(msg.role, 0) + 1
        
        return {
            'total_messages': len(conversation),
            'total_tokens': tokens,
            'system_messages': role_counts.get('system', 0),
            'user_messages': role_counts.get('user', 0),
            'assistant_messages': role_counts.get('assistant', 0),
            'tool_messages': role_counts.get('tool', 0),
            'avg_tokens_per_message': tokens / len(conversation) if conversation else 0,
            'available_tokens': self.max_context_tokens - self.reserve_tokens - tokens
        }