from typing import List, Optional
from pydantic import BaseModel


class OllamaResponse(BaseModel):
    model: str
    created_at: str
    response: str
    done: bool
    done_reason: Optional[str] = None
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None
