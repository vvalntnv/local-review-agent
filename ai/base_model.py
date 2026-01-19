from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any, Awaitable, List, Optional, Dict


class BaseAIModel(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]]) -> AsyncGenerator[Any, None]:
        pass

    @abstractmethod
    def generate(
        self, prompt: str, context: Optional[List[int]] = None
    ) -> AsyncGenerator[Any, None]:
        pass

    # @abstractmethod
    # async def generate(
    #     self, prompt: str, context: Optional[List[int]] = None
    # ) -> AsyncGenerator[Any, None]:
    #     pass
