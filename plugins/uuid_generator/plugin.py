"""
UUID Generator plugin - Generate unique identifiers.
"""
from src.tools.base import BaseTool, ToolDefinition
import uuid


class UUIDGeneratorTool(BaseTool):
    """UUID Generator tool."""
    
    def get_definition(self) -> ToolDefinition:
        """Get tool definition."""
        return ToolDefinition(
            name="generate_uuid",
            description="Generate a random UUID (Universally Unique Identifier). Can generate UUID4 (random), UUID1 (timestamp-based), or formatted versions.",
            parameters={
                "type": "object",
                "properties": {
                    "version": {
                        "type": "string",
                        "description": "UUID version to generate: 'uuid4' (random, default) or 'uuid1' (timestamp-based)",
                        "enum": ["uuid4", "uuid1"]
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format: 'standard' (with hyphens), 'hex' (no hyphens), or 'urn' (URN format)",
                        "enum": ["standard", "hex", "urn"]
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of UUIDs to generate (1-10, default: 1)",
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": []
            }
        )
    
    async def execute(self, version: str = "uuid4", format: str = "standard", count: int = 1, **kwargs) -> str:
        """Execute the UUID generator."""
        try:
            # Validate count
            count = max(1, min(10, count))
            
            uuids = []
            for _ in range(count):
                # Generate UUID based on version
                if version == "uuid1":
                    generated_uuid = uuid.uuid1()
                else:  # uuid4 (default)
                    generated_uuid = uuid.uuid4()
                
                # Format UUID
                if format == "hex":
                    formatted = generated_uuid.hex
                elif format == "urn":
                    formatted = generated_uuid.urn
                else:  # standard (default)
                    formatted = str(generated_uuid)
                
                uuids.append(formatted)
            
            # Build response
            if count == 1:
                return f"🔑 Generated UUID ({version}, {format}):\n```\n{uuids[0]}\n```"
            else:
                uuid_list = "\n".join(uuids)
                return f"🔑 Generated {count} UUIDs ({version}, {format}):\n```\n{uuid_list}\n```"
            
        except Exception as e:
            return f"❌ Error generating UUID: {str(e)}"


class Plugin:
    """Main plugin class."""
    
    def __init__(self):
        """Initialize the plugin."""
        self.tools = [UUIDGeneratorTool()]
    
    def get_tools(self):
        """Get tools provided by this plugin."""
        return self.tools
    
    def cleanup(self):
        """Cleanup when plugin is unloaded."""
        pass
