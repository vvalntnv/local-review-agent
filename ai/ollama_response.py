from typing import List, Optional
from pydantic import BaseModel


class BaseOllamaResponse(BaseModel):
    model: str
    created_at: str
    done: bool
    done_reason: Optional[str] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


class OllamaResponse(BaseOllamaResponse):
    response: str
    context: Optional[List[int]] = None


class UserMessage(BaseModel):
    role: str
    content: str
    images: Optional[List[str]] = None


class OllamaMessage(UserMessage):
    tool_calls: Optional[List[dict]] = None


class OllamaChatResponse(BaseOllamaResponse):
    message: OllamaMessage
