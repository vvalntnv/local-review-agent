from pydantic import BaseModel

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

    def get_todos(self) -> list[ToDoItem]:
        return self._get_todos()

    def _call_tool(self, tool_call: ToolCall) -> ToolResult:
        has_tool = hasattr(self, tool_call.function.name)

        if has_tool:
            callable = getattr(self, tool_call.function.name)
            try:
                callable(**tool_call.function.arguments)
                return ToolResult(ok=True, err=None)
            except Exception as e:
                return ToolResult(ok=None, err=e)

        return super()._call_tool(tool_call)  # type: ignore

    def _get_todos(self) -> list[ToDoItem]:
        return getattr(self, "todos")
