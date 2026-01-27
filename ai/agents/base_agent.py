from abc import ABC, abstractmethod
from ai.base_model import BaseAIModel
from ai.message import AgentMessage
from ai.tool_definitions import Tool, ToolCall, ToolResult
from program_state import ProgramState
from tools import TOOLS
from tools.todos import ToDoItem


class BaseAgent(ABC):
    def __init__(self, ai_model: BaseAIModel, tools: list[Tool]) -> None:
        self.model = ai_model
        self.tools = [tool.model_dump() for tool in tools]
        self.messages: list[AgentMessage] = []
        self.todos: list[ToDoItem] = []

    @abstractmethod
    async def invoke(
        self,
    ) -> ProgramState:
        pass

    def add_user_message(self, user_message: AgentMessage) -> None:
        self.messages.append(user_message)

    def _get_user_last_message(self):
        for message in reversed(self.messages):
            if message["role"] == "user":
                return message

        return None

    def _call_tool(self, tool_call: ToolCall) -> ToolResult:
        tool = TOOLS.get(tool_call.function.name)
        if not tool:
            return ToolResult(ok=None, err=Exception("No tool selected"))
        try:
            result = tool(**tool_call.function.arguments)
            return ToolResult(ok=result, err=None)
        except Exception as e:
            return ToolResult(ok=None, err=e)

    def _get_undone_todos(self) -> list[ToDoItem]:
        return [todo for todo in self.todos if not todo.is_complete]

    def _get_done_todos(self) -> list[ToDoItem]:
        return [todo for todo in self.todos if not todo.is_complete]

    def _get_all_todos(self) -> list[ToDoItem]:
        return self.todos
