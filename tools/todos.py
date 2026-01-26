from pydantic import BaseModel

from ai.agents.base_agent import BaseAgent
from ai.tool_definitions import ToolCall, ToolResult


class ToDoItem(BaseModel):
    requirement: str
    is_complete: bool


class SupportsToDoMixin:
    def __init__(self) -> None:
        assert hasattr(self, "todos")
        todos = getattr(self, "todos")
        assert isinstance(todos, list)

    def write_todos(self, requirements: list[str]) -> None:
        # This should be a reference
        todos = self._get_todos()
        for requirement in requirements:
            todos.append(ToDoItem(requirement=requirement, is_complete=False))

    def update_todo(self, todo_id: int, new_status: bool) -> None:
        todos = self._get_todos()
        todos[todo_id].is_complete = new_status

    def remove_todo(self, todo_id: int) -> None:
        todos = self._get_todos()
        todos.pop(todo_id)

    def _call_tool(self, tool_call: ToolCall) -> ToolResult:
        has_tool = hasattr(self, tool_call.function.name)

        if has_tool:
            callable = getattr(self, tool_call.function.name)
            try:
                callable(self, tool_call.function.arguments)
                return ToolResult(ok=True, err=None)
            except Exception as e:
                return ToolResult(ok=None, err=e)

        assert hasattr(self, "_call_tool")
        _call_tool_method = getattr(self, "_call_tool")
        return _call_tool_method(tool_call)

    def _get_todos(self) -> list[ToDoItem]:
        return getattr(self, "todos")
