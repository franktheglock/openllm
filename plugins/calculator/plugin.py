"""
Calculator plugin - Perform mathematical calculations.
"""
from src.tools.base import BaseTool, ToolDefinition
import ast
import operator


class CalculatorTool(BaseTool):
    """Calculator tool for evaluating mathematical expressions."""
    
    # Supported operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }
    
    def get_definition(self) -> ToolDefinition:
        """Get tool definition."""
        return ToolDefinition(
            name="calculate",
            description="Evaluate a mathematical expression. Supports +, -, *, /, **, %, // operators and parentheses. Example: '2 + 2', '(10 * 5) / 2', '2 ** 8'",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate (e.g., '2 + 2', '10 * 5 / 2')"
                    }
                },
                "required": ["expression"]
            }
        )
    
    def _safe_eval(self, node):
        """Safely evaluate an AST node."""
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise ValueError(f"Unsupported operation: {op_type.__name__}")
            return self.OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand)
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise ValueError(f"Unsupported operation: {op_type.__name__}")
            return self.OPERATORS[op_type](operand)
        elif isinstance(node, ast.Expression):
            return self._safe_eval(node.body)
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")
    
    async def execute(self, expression: str, **kwargs) -> str:
        """Execute the calculator."""
        try:
            # Remove whitespace
            expression = expression.strip()
            
            # Parse the expression
            tree = ast.parse(expression, mode='eval')
            
            # Evaluate safely
            result = self._safe_eval(tree)
            
            # Format result
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            
            return f"**{expression}** = **{result}**"
            
        except ZeroDivisionError:
            return "❌ Error: Division by zero"
        except SyntaxError:
            return f"❌ Error: Invalid mathematical expression. Please use valid math operators (+, -, *, /, **, %, //) and parentheses."
        except ValueError as e:
            return f"❌ Error: {str(e)}"
        except Exception as e:
            return f"❌ Error evaluating expression: {str(e)}"


class Plugin:
    """Main plugin class."""
    
    def __init__(self):
        """Initialize the plugin."""
        self.tools = [CalculatorTool()]
    
    def get_tools(self):
        """Get tools provided by this plugin."""
        return self.tools
    
    def cleanup(self):
        """Cleanup when plugin is unloaded."""
        pass
