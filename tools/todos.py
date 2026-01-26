from pydantic import BaseModel

from ai.agents.base_agent import BaseAgent


class ToDoItem(BaseModel):
    requirement: str
    is_complete: bool


class SupportsToDoMixin:
    def __init__(self) -> None:
        assert hasattr(self, "todos")
        todos = getattr(self, "todos")
        assert isinstance(todos, list)

    def write_todo(self, requirement: str) -> None:
        # This should be a reference
        todos = self._get_todos()
        todos.append(ToDoItem(requirement=requirement, is_complete=False))

    def update_todo(self, todo_id: int, new_status: bool) -> None:
        todos = self._get_todos()
        todos[todo_id].is_complete = new_status

    def remove_todo(self, todo_id: int) -> None:
        todos = self._get_todos()
        todos.pop(todo_id)

    def _get_todos(self) -> list[ToDoItem]:
        return getattr(self, "todos")
