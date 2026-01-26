from enum import Enum


class ProgramState(str, Enum):
    USER_CONTROL = "UserControl"
    AGENT_CONTROL = "AgentControl"
