# Plugin Development Guide

This guide will help you create custom plugins to extend the Discord LLM Bot's functionality.

## Plugin Structure

A plugin is a directory containing at least two files:

```
my_plugin/
├── manifest.json    # Plugin metadata and configuration
└── plugin.py        # Main plugin code
```

## Manifest File

The `manifest.json` file describes your plugin:

```json
{
  "name": "My Custom Plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "A brief description of what your plugin does",
  "permissions": ["network", "storage"],
  "tools": [
    {
      "name": "my_tool",
      "description": "What this tool does"
    }
  ],
  "entry_point": "plugin.py"
}
```

### Required Fields

- `name`: Display name of your plugin
- `version`: Semantic version (e.g., "1.0.0")
- `author`: Your name or organization
- `description`: What your plugin does

### Optional Fields

- `permissions`: List of permissions needed (see Permissions section)
- `tools`: List of tools provided by the plugin
- `entry_point`: Main Python file (default: "plugin.py")

## Plugin Code

Your `plugin.py` file must contain a `Plugin` class:

```python
from src.tools.base import BaseTool, ToolDefinition


class MyCustomTool(BaseTool):
    """Your custom tool implementation."""
    
    def get_definition(self) -> ToolDefinition:
        """Define the tool for LLM function calling."""
        return ToolDefinition(
            name="my_tool",
            description="What your tool does - be specific!",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Input parameter description"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Optional parameter",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )
    
    async def execute(self, query: str, count: int = 5, **kwargs) -> str:
        """
        Execute your tool logic.
        
        Args:
            query: The search query
            count: Number of results
        
        Returns:
            Result string that will be sent back to the LLM
        """
        # Your tool logic here
        result = f"Processed: {query} with count {count}"
        return result


class Plugin:
    """Main plugin class - REQUIRED."""
    
    def __init__(self):
        """Initialize your plugin."""
        self.tools = [MyCustomTool()]
        # Initialize any resources you need
    
    def get_tools(self):
        """Return list of tools provided by this plugin."""
        return self.tools
    
    def cleanup(self):
        """
        Optional: Cleanup when plugin is unloaded.
        Close connections, save state, etc.
        """
        pass
```

## Tool Development

### Tool Definition

The `get_definition()` method defines how the LLM can call your tool. Use JSON Schema to specify parameters:

```python
def get_definition(self) -> ToolDefinition:
    return ToolDefinition(
        name="weather_tool",
        description="Get current weather for a location. Use this when users ask about weather.",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or zip code"
                },
                "units": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature units",
                    "default": "celsius"
                }
            },
            "required": ["location"]
        }
    )
```

### Tool Execution

The `execute()` method performs the actual work:

```python
async def execute(self, location: str, units: str = "celsius", **kwargs) -> str:
    """
    Execute the tool.
    
    Important:
    - Must be async (use 'async def')
    - Parameters must match your definition
    - Return a string that will be sent to the LLM
    - Handle errors gracefully
    """
    try:
        # Your logic here
        # Example: Call an API
        weather_data = await fetch_weather(location, units)
        
        # Format result for the LLM
        result = f"Weather in {location}: {weather_data['temp']}°{units[0].upper()}, {weather_data['conditions']}"
        return result
    
    except Exception as e:
        return f"Error fetching weather: {str(e)}"
```

## Permissions

Plugins can request permissions:

### Available Permissions

- `network`: Make HTTP requests
- `storage`: Read/write files
- `discord_api`: Access Discord API directly

### Requesting Permissions

In your `manifest.json`:

```json
{
  "permissions": ["network", "storage"]
}
```

### Using Permissions

```python
import aiohttp

class MyTool(BaseTool):
    async def execute(self, url: str, **kwargs) -> str:
        # This requires 'network' permission
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.text()
                return data
```

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
async def execute(self, **kwargs) -> str:
    try:
        result = await do_something()
        return result
    except ValueError as e:
        return f"Invalid input: {str(e)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"
```

### 2. Clear Descriptions

Make tool descriptions clear for the LLM:

```python
# ❌ Bad
description="Does stuff"

# ✅ Good
description="Searches Wikipedia for articles matching the query and returns a summary. Use this when users ask for factual information about topics, people, or events."
```

### 3. Type Hints

Use proper type hints:

```python
async def execute(self, query: str, limit: int = 10, **kwargs) -> str:
    # Clear parameter types
    pass
```

### 4. Async/Await

Tools should be async to not block the bot:

```python
# ❌ Bad - blocking
def execute(self, **kwargs) -> str:
    time.sleep(5)  # Blocks the entire bot!
    return "done"

# ✅ Good - async
async def execute(self, **kwargs) -> str:
    await asyncio.sleep(5)  # Doesn't block
    return "done"
```

## Testing Your Plugin

### 1. Install in Development

Place your plugin in the `plugins/` directory:

```
plugins/
└── my_plugin/
    ├── manifest.json
    └── plugin.py
```

### 2. Enable in Config

Ensure plugins are enabled in `config.yaml`:

```yaml
plugins:
  enabled: true
  auto_load: true
  allowed_permissions:
    - network
    - storage
```

### 3. Test with Bot

Start the bot and test your tool:

```
@BotName use my_tool with query "test"
```

The LLM will automatically call your tool when appropriate.

## Examples

### Example 1: Simple Calculation Tool

```python
from src.tools.base import BaseTool, ToolDefinition
import math


class CalculatorTool(BaseTool):
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="calculator",
            description="Perform mathematical calculations. Supports +, -, *, /, ^, sqrt, etc.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)')"
                    }
                },
                "required": ["expression"]
            }
        )
    
    async def execute(self, expression: str, **kwargs) -> str:
        try:
            # Safe evaluation (be careful with eval!)
            result = eval(expression, {"__builtins__": {}}, {
                "sqrt": math.sqrt,
                "pow": math.pow,
                "abs": abs,
                "round": round
            })
            return f"Result: {result}"
        except Exception as e:
            return f"Error calculating: {str(e)}"


class Plugin:
    def __init__(self):
        self.tools = [CalculatorTool()]
    
    def get_tools(self):
        return self.tools
```

### Example 2: API Integration Tool

```python
from src.tools.base import BaseTool, ToolDefinition
import aiohttp


class NewsSearchTool(BaseTool):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="news_search",
            description="Search for recent news articles about a topic",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for news"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of articles to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )
    
    async def execute(self, query: str, limit: int = 5, **kwargs) -> str:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "pageSize": limit,
            "apiKey": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                if data.get("status") != "ok":
                    return "Error fetching news"
                
                articles = data.get("articles", [])
                
                if not articles:
                    return "No news found"
                
                result = "Recent news:\n\n"
                for article in articles[:limit]:
                    result += f"• {article['title']}\n"
                    result += f"  {article['description']}\n\n"
                
                return result


class Plugin:
    def __init__(self):
        # Get API key from environment or config
        import os
        api_key = os.getenv("NEWS_API_KEY", "")
        self.tools = [NewsSearchTool(api_key)]
    
    def get_tools(self):
        return self.tools
```

## Publishing Your Plugin

Once your plugin is ready:

1. Test thoroughly
2. Write clear documentation
3. Add a README.md to your plugin directory
4. Consider sharing it with the community!

## Troubleshooting

### Plugin Not Loading

- Check manifest.json is valid JSON
- Ensure Plugin class exists in entry_point file
- Check logs for error messages

### Tool Not Being Called

- Make description very clear about when to use it
- Check parameter schema is valid JSON Schema
- Test with explicit user requests

### Permission Denied

- Add required permissions to manifest.json
- Ensure permissions are in allowed list in config.yaml

## Support

For help with plugin development:
- Check example plugins in `plugins/` directory
- Review bot logs for error messages
- Refer to the main README.md
