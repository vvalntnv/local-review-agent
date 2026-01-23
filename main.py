import asyncio
import logging
from ai.agents.code_review import CodeReviewAgent
from ai.message import Message
from ai.tool_definitions import generate_ollama_tools
from db.database import DatabaseManager
from db.models import Chat
from ai.communication import OllamaApiClient

log = logging.getLogger("main")
log.setLevel(logging.DEBUG)


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
        tools = generate_ollama_tools()
        review_agent = CodeReviewAgent(
            client,
            "You are a pro at doing review",
            tools=tools,
        )

        messages: list[Message] = []
        total_loops = 0
        ask_user = False
        while True:
            user_request = input("\nWhat should the agent review?")
            messages.append(
                {
                    "role": "user",
                    "content": user_request,
                    "images": None,
                    "tool_calls": None,
                }
            )

            ask_user = False

            while not ask_user:
                if total_loops > 10:
                    raise Exception(
                        "qvno bratleto e tupo, moje bi shte e"
                        "po-dobre da si go svurshihs sam bratle ;P"
                    )
                messages, ask_user = await review_agent.invoke(messages)
                log.debug(messages)


if __name__ == "__main__":
    asyncio.run(main())
