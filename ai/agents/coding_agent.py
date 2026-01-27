from typing import Any
from pydantic import ValidationError
from ai.agents.base_agent import BaseAgent
from ai.agents.decisions import AgentDecision
from ai.base_model import BaseAIModel
from ai.ollama_response import OllamaResponse
from ai.tool_definitions import Tool, ToolCall
from program_state import ProgramState
from tools.todos import SupportsToDoMixin

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


class CodeReviewAgent(SupportsToDoMixin, BaseAgent):
    def __init__(self, ai_model: BaseAIModel, tools: list[Tool]) -> None:
        super().__init__(ai_model, tools)
        self.todos_created = False
        self.messages.extend(
            [
                {
                    "content": CODING_AGENT_INSTRUCTIONS,
                    "role": "system",
                    "images": None,
                    "tool_calls": None,
                },
                {
                    "content": "You should always create todos first. So call the todo tool and create some todos before you ever thing about proceeding with the task, no matter what the user demands. Here is an example todo list: 1. Explore the file structure 2. Open key files.\n And later on, you might get rid of 1 and 2, with remove_todo tool and add another one. Like: 1. Look into the main.py file 2. Explore the imports one by one 3. Write the review in the Review.md file.\n Only after all the todos are completed you are allowed to stop iterating on the problem",
                    "role": "system",
                    "images": None,
                    "tool_calls": None,
                },
                {
                    "content": "For creating todos, you use the appropriate tools",
                    "role": "system",
                    "images": None,
                    "tool_calls": None,
                },
            ]
        )

    async def invoke(self) -> ProgramState:
        user_message = self._get_user_last_message()

        if not user_message:
            return ProgramState.USER_CONTROL

        # Step 2 is to create to-do list based on the user's task
        # If todos haven't been created yet, enforce todo creation first
        if not self.todos_created:
            if not await self.is_propmt_relevant(user_message["content"]):
                return ProgramState.USER_CONTROL

            response = self.model.chat(self.messages, tools=self.tools)  # type: ignore
            async for next_item in response:
                if tool_calls := next_item.message.tool_calls:
                    tool_call = ToolCall(**tool_calls[0])

                    if tool_call.function.name != "write_todos":
                        print("|nee ok|")
                        # Reject and remind
                        self.messages.append(
                            {
                                "role": "assistant",
                                "content": "You must create todos first using write_todos before proceeding with other tools.",
                                "images": None,
                                "tool_calls": None,
                            }
                        )
                        return ProgramState.AGENT_CONTROL

                    # Execute write_todos
                    tool_res = self._call_tool(tool_call)

                    if not tool_res.is_ok():
                        self.messages.append(
                            {
                                "role": "tool",
                                "content": f"Error creating todos: {tool_res.get_err()}",
                                "images": None,
                                "tool_calls": None,
                            }
                        )
                        return ProgramState.AGENT_CONTROL

                    self.todos_created = True
                    self.messages.append(
                        {
                            "role": "tool",
                            "content": f"Todos created successfully: {len(self.todos)} items",
                            "images": None,
                            "tool_calls": None,
                        }
                    )
                    return ProgramState.AGENT_CONTROL
                else:
                    print(next_item.message.content, end="")

            return ProgramState.USER_CONTROL

        # --- Main Execution Loop ---

        # 1. Check for completion
        if not self._get_undone_todos():
            print("\nAll tasks in the todo list are complete.")
            return ProgramState.USER_CONTROL

        # 2. Generate Model Response
        print("\nThinking...")
        # Convert AgentMessage (TypedDict) to regular dict format for the model
        response = self.model.chat(self.messages, tools=self.tools)  # type: ignore

        content_buffer = ""
        tool_calls = []

        async for chunk in response:
            if chunk.message.content:
                print(chunk.message.content, end="", flush=True)
                content_buffer += chunk.message.content
            if chunk.message.tool_calls:
                tool_calls.extend(chunk.message.tool_calls)

        print()  # Newline for clean output

        # 3. Add Assistant Message to History
        self.messages.append(
            {
                "role": "assistant",
                "content": content_buffer,
                "images": None,
                "tool_calls": tool_calls if tool_calls else None,
            }
        )

        # 4. Execute Tools
        if tool_calls:
            for tc_data in tool_calls:
                tool_call = ToolCall(**tc_data)

                # Execute tool
                result = self._call_tool(tool_call)

                # Add Tool Output to History
                self.messages.append(
                    {
                        "role": "tool",
                        "content": (
                            str(result.get_val())
                            if result.is_ok()
                            else f"Error: {result.get_err()}"
                        ),
                        "images": None,
                        "tool_calls": None,
                    }
                )

            # Continue autonomous execution
            return ProgramState.AGENT_CONTROL

        # 5. Hand back to user if no tools were called (e.g. asking a question)
        return ProgramState.USER_CONTROL

    async def is_propmt_relevant(self, prompt: str) -> bool:
        complete_prompt = (
            "You are: \n"
            + CODING_AGENT_INSTRUCTIONS
            + "Based on that fact, tell if the prompt bellow is relevant and with what certainty\n"
            + prompt
        )
        # a defacto DecisionNode for SBK
        response: OllamaResponse = await anext(
            self.model.generate(complete_prompt, structure=AgentDecision)
        )
        try:
            value = AgentDecision.model_validate_json(response.response)
            return value.should_do and value.confidence > 0.5
        except ValidationError as e:
            print("model is dumb af")
            raise e
