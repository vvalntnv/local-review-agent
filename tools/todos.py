from pydantic import BaseModel

from ai.agents.base_agent import BaseAgent


class ToDoItem(BaseModel):
    requirement: str
    is_complete: bool

todo_tool_definition = {}
