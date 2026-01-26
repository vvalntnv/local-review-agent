from typing import Literal, Optional, TypedDict


class AgentMessage(TypedDict):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    images: Optional[list[str]]
    tool_calls: Optional[list[dict]]
