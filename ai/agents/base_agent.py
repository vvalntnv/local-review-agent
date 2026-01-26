from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from ai.base_model import BaseAIModel
from ai.message import AgentMessage
from ai.tool_definitions import Tool
from program_state import ProgramState

if TYPE_CHECKING:
    from tools.todos import ToDoItem


class BaseAgent(ABC):
    def __init__(self, ai_model: BaseAIModel, tools: list[Tool]) -> None:
        self.model = ai_model
        self.tools = [tool.model_dump() for tool in tools]
        self.messages: list[AgentMessage] = []
        self.todos: list["ToDoItem"] = []

    @abstractmethod
    async def invoke(
        self,
    ) -> ProgramState:
        pass

    def _get_user_last_message(self):
        for message in reversed(self.messages):
            if message["role"] == "user":
                return message

        return None
