import json
from typing import Callable

from pydantic import BaseModel
from ai.agents.base_agent import BaseAgent
from ai.base_model import BaseAIModel
from ai.message import AgentMessage
from ai.tool_definitions import Tool, ToolCall
from tools import TOOLS

CODING_AGENT_INSTRUCTIONS = """
You are a Python code reviewer. Your job is to inspect a repository and report bad practices, bugs, and refactors, and suggest cleaner implementations.

Hard rules:
1) Never read or reveal secrets. Never open or print the contents of any .env file.
2) Always ignore the following paths/names when scanning:
   - .git
   - __pycache__
   - any file named .env
3) When calling explore_structure, ALWAYS pass ignore_names as a JSON array of regex strings (type: array of strings). Never pass ignore_names as a single string.
4) Tool-call arguments MUST be valid JSON and MUST match the tool schema types exactly (integers as numbers, arrays as JSON arrays, etc).

For explore_structure, use:
{
  "root_dir_path": ".",
  "depth": 5,
  "ignore_names": ["^\\.git$", "^__pycache__$", "^\\.env$", "^\\.env\\..*$"]
}

Notes:
- Ignore patterns must be valid regex.
- If you are unsure what to do next, explore the structure first.

Some info about the tools
explore_structure:
When you receive the output of explore_structure:
- Treat it as the project file tree.
- Do not ask the user what to do with it.
"""


class ToolRetryTracker:
    def __init__(self, max_retries: int = 3):
        self.attempts: dict[str, int] = {}
        self.max_retries = max_retries

    def should_retry(self, tool_name: str) -> bool:
        count = self.attempts.get(tool_name, 0)
        return count < self.max_retries

    def record_attempt(self, tool_name: str):
        self.attempts[tool_name] = self.attempts.get(tool_name, 0) + 1


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
        self.retry_tracker = ToolRetryTracker()

    async def invoke(
        self, messages: list[AgentMessage]
    ) -> tuple[list[AgentMessage], bool]:
        # I know its dirty, its just a prototype
        should_give_back_control = True

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
                print(content, end="", flush=True)
                current_content += content

            if chunk.message.tool_calls:
                tools.extend([ToolCall(**tool) for tool in chunk.message.tool_calls])

        print()  # Newline after streaming completes

        if tools:
            print(f"\n🔧 Calling {len(tools)} tool(s)...")

        if tools:
            should_give_back_control = False
            result, is_success = await self.call_tool(tools)
            message_predicate = (
                "The tool failed... I should try and call the tool again, "
                "this time with keeping the error in mind. "
                "I should invoke the tool again. \n"
                "Maybe the error will tell me if I have something wrong "
                "in the parameters passed: "
                if not is_success
                else ""
            )

            tool_result: AgentMessage = {
                "role": "tool",
                "content": result,
                "images": None,
                "tool_calls": None,
            }
            messages.append(tool_result)

            if not is_success:
                # Record attempt for retry tracking
                self.retry_tracker.record_attempt("tool_execution")

                # Check if we should give up and return control to user
                if not self.retry_tracker.should_retry("tool_execution"):
                    return messages, True  # Give control back to user

                model_message: AgentMessage = {
                    "role": "assistant",
                    "content": message_predicate + result,
                    "images": None,
                    "tool_calls": None,
                }
                messages.append(model_message)

        return messages, should_give_back_control

    async def call_tool(self, tools_to_call: list[ToolCall]) -> tuple[str, bool]:
        results = []

        for tool in tools_to_call:
            print(f"calling tool: {tool.function.name}")
            tool_function = TOOLS.get(tool.function.name)

            if not tool_function:
                results.append(f"ERROR: Tool '{tool.function.name}' does not exist!")
                continue

            result, is_success = self.try_to_call_tool(
                tool_function,
                tool.function.arguments,
            )

            status = "✓" if is_success else "✗"
            results.append(f"{status} {tool.function.name}: {result}")

            if not is_success:
                return ("\n".join(results), False)

        if not results:
            return ("No tools executed", False)

        return ("\n".join(results), True)

    def try_to_call_tool(self, function: Callable, kwargs: dict) -> tuple[str, bool]:
        try:
            result = function(**kwargs)

            if isinstance(result, BaseModel):
                result = result.model_dump_json()
            elif isinstance(result, dict):
                result = json.dumps(result)
            elif not isinstance(result, str):
                try:
                    result = str(result)
                except Exception:
                    return ("TOOL RESULT WITH WRONG TYPE", False)

            return (result, True)

        except Exception as e:
            message = "While calling the tool, we encountered an error: " + str(e)
            return (message, False)
