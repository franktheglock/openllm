"""
Example plugin demonstrating the plugin system.
"""
from src.tools.base import BaseTool, ToolDefinition


class ExampleTool(BaseTool):
    """Example tool implementation."""
    
    def get_definition(self) -> ToolDefinition:
        """Get tool definition."""
        return ToolDefinition(
            name="example_tool",
            description="An example tool that returns a greeting",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name to greet"
                    }
                },
                "required": ["name"]
            }
        )
    
    async def execute(self, name: str, **kwargs) -> str:
        """Execute the tool."""
        return f"Hello, {name}! This is an example tool from a plugin."


class Plugin:
    """Main plugin class."""
    
    def __init__(self):
        """Initialize the plugin."""
        self.tools = [ExampleTool()]
    
    def get_tools(self):
        """Get tools provided by this plugin."""
        return self.tools
    
    def cleanup(self):
        """Cleanup when plugin is unloaded."""
        pass
