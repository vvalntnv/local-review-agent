import json
from pydantic import BaseModel
from ai.agents.base_agent import BaseAgent
from ai.base_model import BaseAIModel
from ai.message import Message
from ai.tool_definitions import Tool, ToolCall
from tools import TOOLS

CODING_AGENT_INSTRUCTIONS = """
    YOU ARE A PROFOUND DEVELOPER, looking at code and trying to search
    for bad practices and suggesting a new clean-code version
    """


class CodeReviewAgent(BaseAgent):
    def __init__(
        self,
        model: BaseAIModel,
        instructions: str,
        tools: list[Tool],
    ) -> None:
        self.model = model
        self.instructions = instructions
        self.tools = [tool.model_dump() for tool in tools]

    async def invoke(self, messages: list[Message]):
        # I know its dirty, its just a prototype
        if len(messages) <= 1:
            messages.insert(
                0,
                {
                    "role": "system",
                    "content": CODING_AGENT_INSTRUCTIONS,
                    "images": [],
                    "tool_calls": None,
                },
            )

            if self.instructions:
                messages.insert(
                    1,
                    {
                        "role": "system",
                        "content": self.instructions,
                        "images": [],
                        "tool_calls": None,
                    },
                )

        stream = self.model.chat(messages, self.tools)  # type: ignore

        tools: list[ToolCall] = []
        current_content = ""
        async for chunk in stream:
            content = chunk.message.content

            if content:
                print(content, sep="", end="")
                current_content += content

            if chunk.message.tool_calls:
                tools.extend([ToolCall(**tool) for tool in chunk.message.tool_calls])

        breakpoint()
        if tools:
            for tool_call in tools:
                if tool_call.type == "function":
                    tool_to_call = TOOLS[tool_call.function.name]
                    result = tool_to_call(tool_call.function.arguments)

                    if isinstance(result, BaseModel):
                        result = json.dumps(result.model_dump())
                    elif not isinstance(result, (str, int, float)):
                        raise Exception("type not ok bro")

                    messages.append(
                        {
                            "role": "tool",
                            "content": str(result),
                            "images": None,
                            "tool_calls": [tool_call.model_dump()],
                        }
                    )
        else:
            last_message: Message = {
                "role": "agent",
                "content": current_content,
                "tool_calls": None,
                "images": None,
            }

            messages.append(last_message)

        return messages
