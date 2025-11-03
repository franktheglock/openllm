"""
Base tool interface.
All tools must implement this interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ToolDefinition:
    """Definition of a tool for LLM function calling."""
    name: str
    description: str
    parameters: Dict[str, Any]


class BaseTool(ABC):
    """Base class for all tools."""
    
    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """
        Get the tool definition for LLM function calling.
        
        Returns:
            ToolDefinition object
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
        
        Returns:
            Result as a string
        """
        pass
    
    def to_openai_tool(self) -> Dict[str, Any]:
        """
        Convert tool definition to OpenAI function calling format.
        
        Returns:
            OpenAI tool definition
        """
        definition = self.get_definition()
        return {
            'type': 'function',
            'function': {
                'name': definition.name,
                'description': definition.description,
                'parameters': definition.parameters
            }
        }
