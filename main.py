import asyncio
from db.database import DatabaseManager
from db.models import Chat
from ai.communication import OllamaApiClient


async def main() -> None:
    db_manager = DatabaseManager()
    db_manager.init_models()

    # Example DB usage
    with db_manager.get_session() as session:
        chat = session.get(Chat, 1)

        if chat is None:
            print("No chats yet bro")
        else:
            print(chat.name)

    # Example AI usage
    with OllamaApiClient("localhost:11434", "llama3.2") as client:
        print("\nSending request to AI...")
        # Note: generate returns an AsyncGenerator, we need to iterate or collect it.
        # Here we just print chunks as they arrive.
        async for chunk in client.generate("Am I pretty?"):
            print(chunk.response, end="", flush=True)
        print()


if __name__ == "__main__":
    asyncio.run(main())
