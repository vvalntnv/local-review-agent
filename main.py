import asyncio
from database import DatabaseManager
from models import Chat


async def main() -> None:
    db_manager = DatabaseManager()
    db_manager.init_models()

    with db_manager.get_session() as session:
        chat = session.get(Chat, 1)

        if chat is None:
            print("No chats yet bro")
        else:
            print(chat.name)


if __name__ == "__main__":
    asyncio.run(main())
