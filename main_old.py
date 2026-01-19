import asyncio
from ai.communication import OllamaApiClient
from ai.ollama_response import Message, UserMessage


async def main() -> None:
    context = None

    with OllamaApiClient("localhost:11434", model="llama3.2:latest") as api_client:
        while True:
            user_request = input("enter the message, or type exit to exit: ")
            if user_request == "exit":
                break

            async for response in api_client.generate(user_request, context):
                print(response.response, sep="", end="")
                if response.done:
                    context = response.context


async def main_with_tools() -> None:
    messages: list[dict] = []

    with OllamaApiClient("localhost:11434", model="llama3.2:latest") as api_client:
        while True:
            user_request = input("Please enter your request. Type 'exit' to exit: ")
            if user_request == "exit":
                break

            user_message = UserMessage(role="user", content=user_request)
            messages.append(user_message.model_dump())

            assistant_message = None
            current_content = ""
            tools = []
            async for response in api_client.chat(messages):
                print(response.message.content, sep="", end="")
                current_content += response.message.content

                if response.message.tool_calls:
                    tools.append(response.message.tool_calls[0])

                if response.done:
                    assistant_message = Message(
                        role=response.message.role, content=current_content
                    )

            if assistant_message:
                messages.append(assistant_message.model_dump())


if __name__ == "__main__":
    asyncio.run(main_with_tools())
