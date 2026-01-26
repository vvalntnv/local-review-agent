from abc import ABC, abstractmethod
from ai.message import AgentMessage


class BaseAgent(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    async def invoke(
        self, messages: list[AgentMessage]
    ) -> tuple[list[AgentMessage], bool]:
        pass
