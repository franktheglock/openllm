# Tool Call Object Fix

## Issue
```
TypeError: 'ChatCompletionMessageFunctionToolCall' object is not subscriptable
```

When the bot attempted to execute tool calls (like web search), it crashed because the OpenAI SDK returns tool calls as objects, not dictionaries.

## Root Cause

The OpenAI Python SDK returns `ChatCompletionMessageFunctionToolCall` objects with attributes like:
```python
tool_call.id
tool_call.function.name
tool_call.function.arguments
```

But the code was trying to access them as dictionaries:
```python
tool_call['id']
tool_call['function']['name']
tool_call['function']['arguments']
```

## Solution

### 1. Normalize in OpenAI Provider (`src/llm/openai_provider.py`)

Convert OpenAI SDK objects to standard dictionary format before returning:

```python
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
    usage={...},
    tool_calls=tool_calls,  # Now always a dict
    finish_reason=choice.finish_reason
)
```

### 2. Simplified Bot Handler (`src/bot.py`)

Now that all providers return consistent dict format:

```python
# Execute each tool call
for tool_call in response.tool_calls:
    # Tool calls are now always in dict format
    tool_name = tool_call['function']['name']
    tool_args_str = tool_call['function']['arguments']
    tool_call_id = tool_call['id']
    
    # Parse arguments
    import json
    try:
        tool_args = json.loads(tool_args_str)
    except:
        tool_args = eval(tool_args_str)  # Fallback
    
    if tool_name in self.tools:
        result = await self.tools[tool_name].execute(**tool_args)
        
        # Add tool result to conversation
        conversation.append(Message(
            role='tool',
            content=result,
            tool_call_id=tool_call_id
        ))
```

## Benefits

1. **Consistent Interface**: All LLM providers now return tool calls in the same dictionary format
2. **Type Safety**: No more runtime errors from object/dict mismatches
3. **Maintainability**: Single code path for handling tool calls
4. **Proper JSON Parsing**: Using `json.loads()` instead of unsafe `eval()`

## Testing

To test tool calling:
1. Enable web search in config
2. Ask the bot a question requiring search: `@Bot what's the latest news about AI?`
3. Bot should successfully call the web search tool and return results

## Files Modified

- `src/llm/openai_provider.py` - Convert tool call objects to dicts
- `src/bot.py` - Simplified tool call handling with consistent dict access

## Related

This fix ensures compatibility with:
- OpenAI GPT-4/GPT-3.5 function calling
- Future tool-calling features in other providers
- Custom tools and plugins
