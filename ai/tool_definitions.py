from dataclasses import dataclass
import inspect
import re
from typing import Any, Callable, Dict, List, Optional, Union, get_type_hints
from pydantic import BaseModel, Field
from tools import TOOLS


class ToolFunction(BaseModel):
    """Represents a function definition for tool calling"""

    name: str = Field(..., description="The name of the function")
    description: str = Field(..., description="Description of what the function does")
    parameters: Dict[str, Any] = Field(
        ..., description="JSON schema for function parameters"
    )


class Tool(BaseModel):
    """Represents a tool that can be called by the model"""

    type: str = Field(
        default="function",
        description="Type of tool (currently only 'function' is supported)",
    )
    function: ToolFunction = Field(..., description="Function definition")


class ToolCallFunction(BaseModel):
    """Function part of a tool call"""

    name: str = Field(..., description="Name of the function to call")
    description: Optional[str] = Field(None, description="Description of the function")
    arguments: Dict[str, Any] = Field(
        ..., description="Arguments to pass to the function"
    )


class ToolCall(BaseModel):
    """Represents a tool call made by the model"""

    type: str = Field(default="function", description="Type of tool call")
    function: ToolCallFunction = Field(..., description="Function call details")


@dataclass
class ToolResult:
    ok: Any | None
    err: Exception | None

    def is_ok(self) -> bool:
        return self.ok is not None and self.err is None

    def get_val(self) -> Any:
        assert self.ok is not None

        return self.ok

    def get_err(self) -> Exception:
        assert self.err is not None

        return self.err


# THE CODE BELOW IS AI GARBAGE!!!!
# ||||||||||||||||||||||||||||||||
# VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV


def _python_type_to_json_schema(python_type: type) -> Dict[str, Any]:
    """Convert Python type to JSON schema definition"""
    if python_type is str:
        return {"type": "string"}
    elif python_type is int:
        return {"type": "integer"}
    elif python_type is float:
        return {"type": "number"}
    elif python_type is bool:
        return {"type": "boolean"}
    elif python_type is type(None):
        return {"type": "null"}
    elif hasattr(python_type, "__origin__"):
        # Handle typing constructs like List, Union, etc.
        origin = python_type.__origin__
        if origin is list:
            item_type = python_type.__args__[0] if python_type.__args__ else str
            return {"type": "array", "items": _python_type_to_json_schema(item_type)}
        elif origin == Union:
            # Handle Union types (including Optional)
            args = python_type.__args__
            if len(args) == 2 and type(None) in args:
                # Optional[T] case
                non_none_type = args[0] if args[1] is type(None) else args[1]
                return _python_type_to_json_schema(non_none_type)
            else:
                # Complex Union - use first non-None type
                non_none_types = [arg for arg in args if arg is not type(None)]
                if non_none_types:
                    return _python_type_to_json_schema(non_none_types[0])
    elif inspect.isclass(python_type) and issubclass(python_type, BaseModel):
        # Handle Pydantic models
        return python_type.model_json_schema()

    raise TypeError(
        f"Unsupported parameter type: {python_type}. "
        f"Supported types: str, int, float, bool, List[T], Optional[T], BaseModel"
    )


def _extract_function_description(func: Callable) -> str:
    """Extract and format function description from docstring"""
    docstring = func.__doc__ or ""
    if not docstring.strip():
        return f"Function {func.__name__} - no description available"

    # Clean up docstring
    cleaned = re.sub(r"\s+", " ", docstring.strip())

    # Add examples if we can infer them
    examples = _generate_tool_examples(func)
    if examples:
        cleaned += f"\n\nExamples:\n{examples}"

    return cleaned


def _generate_tool_examples(func: Callable) -> str:
    """Generate usage examples for tools"""
    func_name = func.__name__

    if func_name == "explore_structure":
        return 'explore_structure(root_dir_path="src", depth=2, ignore_names=[r".*\\.pyc$", "__pycache__"])'
    elif func_name == "read_file":
        return 'read_file(file_path="src/main.py")'
    elif func_name == "write_review":
        return 'write_review(review="Excellent code structure", file_to_write="review.txt")'
    elif func_name == "write_todos":
        return 'write_todos(requirements=["Implement feature X", "Write unit tests", "Update documentation"])'
    elif func_name == "update_todo":
        return "update_todo(todo_id=0, new_status=True)"
    elif func_name == "remove_todo":
        return "remove_todo(todo_id=2)"

    return f"{func_name}(...)"


def _create_tool_schema(func: Callable) -> Dict[str, Any]:
    """Create JSON schema for a tool function"""
    try:
        # Get function signature
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        # Build parameter schema
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            param_type = type_hints.get(param_name, str)
            param_schema = _python_type_to_json_schema(param_type)

            # Add description if available
            if param_name == "root_dir_path":
                param_schema["description"] = "The root directory path to explore"
            elif param_name == "depth":
                param_schema["description"] = (
                    "How many levels deep to explore recursively"
                )
                param_schema["default"] = 1
            elif param_name == "ignore_names":
                param_schema["description"] = (
                    "List of regex patterns to ignore when scanning"
                )
            elif param_name == "file_path":
                param_schema["description"] = (
                    "The relative file path to the project to read"
                )
            elif param_name == "review":
                param_schema["description"] = "The review content to write"
            elif param_name == "file_to_write":
                param_schema["description"] = (
                    "The file path where the review should be written"
                )
            elif param_name == "requirements":
                param_schema["description"] = (
                    "List of requirement strings to add as todo items"
                )
            elif param_name == "todo_id":
                param_schema["description"] = (
                    "The index of the todo item in the list (0-based)"
                )
            elif param_name == "new_status":
                param_schema["description"] = (
                    "The new completion status (True for complete, False for incomplete)"
                )
            else:
                param_schema["description"] = f"Parameter {param_name}"

            # Check if parameter has default value
            if param.default != inspect.Parameter.empty:
                param_schema["default"] = param.default
            else:
                required.append(param_name)

            properties[param_name] = param_schema

        return {"type": "object", "properties": properties, "required": required}

    except Exception as e:
        raise ValueError(
            f"Failed to create schema for function {func.__name__}: {str(e)}"
        )


# Tool schema generation using reflection
# Automatically converts Python type hints to JSON Schema for Ollama API
def generate_ollama_tools() -> List[Tool]:
    """
    Dynamically generates Ollama API tool definitions from tools/ directory

    Returns:
        List of Tool objects ready for Ollama API consumption

    Raises:
        ValueError: If a tool cannot be processed properly
    """
    tools = []

    for tool_name, tool_func in TOOLS.items():
        try:
            # Extract function description
            description = _extract_function_description(tool_func)

            # Create parameter schema
            parameters = _create_tool_schema(tool_func)

            # Create tool function definition
            tool_function = ToolFunction(
                name=tool_name, description=description, parameters=parameters
            )

            # Create complete tool
            tool = Tool(type="function", function=tool_function)
            tools.append(tool)

        except Exception as e:
            error_msg = f"Failed to process tool '{tool_name}': {str(e)}"
            print(f"Warning: {error_msg}")
            # Continue processing other tools instead of failing completely
            continue

    if not tools:
        raise ValueError("No valid tools could be generated from the tools/ directory")

    return tools


class LogProbToken(BaseModel):
    """Represents a token with log probability information"""

    token: str = Field(..., description="The token")
    logprob: float = Field(..., description="Log probability of the token")
    bytes: Optional[List[int]] = Field(
        None, description="Byte representation of the token"
    )
