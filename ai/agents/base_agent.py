from abc import ABC, abstractmethod
from ai.message import Message


class BaseAgent(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    async def invoke(self, messages: list[Message]) -> tuple[list[Message], bool]:
        pass
