from pydantic import BaseModel

from ai.tool_definitions import ToolCall, ToolResult
from typing import List


class ToDoItem(BaseModel):
    requirement: str
    is_complete: bool


class SupportsToDoMixin:
    def __init__(self) -> None:
        assert hasattr(self, "todos")
        todos = getattr(self, "todos")
        assert isinstance(todos, list)

    def write_todos(self, requirements: List[str]) -> None:
        # This should be a reference
        todos = getattr(self, "todos")
        for requirement in requirements:
            todos.append(ToDoItem(requirement=requirement, is_complete=False))

    def update_todo(self, todo_id: int, new_status: bool) -> None:
        todos = getattr(self, "todos")
        todos[todo_id].is_complete = new_status

    def remove_todo(self, todo_id: int) -> None:
        todos = getattr(self, "todos")
        todos.pop(todo_id)

    def get_todos(self) -> list:
        return getattr(self, "todos")

    def _call_tool(self, tool_call: ToolCall) -> ToolResult:
        has_tool = hasattr(self, tool_call.function.name)

        if has_tool:
            method = getattr(self, tool_call.function.name)
            try:
                # Methods are already bound, just unpack arguments
                result = method(**tool_call.function.arguments)
                return ToolResult(ok=result, err=None)
            except Exception as e:
                return ToolResult(ok=None, err=e)

        # Call parent class _call_tool for non-todo tools
        # First, check if we have a parent class with _call_tool method
        try:
            # Try to call the parent class's _call_tool method
            parent_class = super()
            if hasattr(parent_class, "_call_tool"):
                return parent_class._call_tool(tool_call)
        except AttributeError:
            pass

        # If no parent _call_tool, we try to use the base implementation
        return ToolResult(ok=None, err=Exception("No tool found"))
