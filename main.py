import asyncio
from ollama_api_client import OllamaApiClient


async def main() -> None:
    api_client = OllamaApiClient("localhost:11434", model="llama3.2:latest")
    context = None

    while True:
        user_request = input("enter the message, or type exit to exit: ")
        if user_request == "exit":
            return

        async for response in api_client.generate_response(user_request, context):
            print(response.response, sep="", end="")
            if response.done:
                context = response.context


if __name__ == "__main__":
    asyncio.run(main())
