from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any, Awaitable, List, Optional, Dict

from pydantic import BaseModel

from .ollama_response import OllamaChatResponse


class BaseAIModel(ABC):
    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, str]]],
    ) -> AsyncGenerator[OllamaChatResponse, None]:
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        context: Optional[List[int]] = None,
        structure: Optional[type[BaseModel]] = None,
    ) -> AsyncGenerator[Any, None]:
        pass

    # @abstractmethod
    # async def generate(
    #     self, prompt: str, context: Optional[List[int]] = None
    # ) -> AsyncGenerator[Any, None]:
    #     pass
