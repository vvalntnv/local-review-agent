from typing import Callable, Literal
from pydantic import BaseModel

from ai.tool_definitions import Tool


class Node(BaseModel): ...


class DecisionNode(Node):
    information_tools: list[Tool]
    left: Node
    right: Node


class ForkNode(Node):
    left: Node
    right: Node
    logic: Callable[..., Literal["left", "right"]]

class ActionNode(Node):
    action_tool: Tool
