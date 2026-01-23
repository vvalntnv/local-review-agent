from typing import Literal, Optional, TypedDict


class Message(TypedDict):
    role: Literal["system", "user", "agent", "tool"]
    content: str
    images: Optional[list[str]]
    tool_calls: Optional[list[dict]]
