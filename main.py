import asyncio
import json
import logging

from sqlalchemy.orm import Session
from ai.agents.coding_agent import CodeReviewAgent

from ai.message import AgentMessage
from ai.tool_definitions import generate_ollama_tools
from db.database import DatabaseManager

from db.models import Chat
from ai.communication import OllamaApiClient
from program_state import ProgramState

log = logging.getLogger("main")
log.setLevel(logging.DEBUG)


async def main() -> None:
    db_manager = DatabaseManager()
    db_manager.init_models()

    def get_or_create_chat(session, name: str = "default") -> Chat:
        # chat = session.query(Chat).filter_by(name=name).first()
        chat = None
        if not chat:
            chat = Chat(name=name, messages=[])
            session.add(chat)
            session.commit()
        return chat

    def save_messages(
        session: Session,
        chat_id: int,
        messages: list[AgentMessage],
    ) -> None:
        chat = session.get(Chat, chat_id)
        if chat:
            chat.messages = messages
            session.commit()

    # Get or create chat for persistence
    with db_manager.get_session() as session:
        chat = get_or_create_chat(session, "code_review_session")
        messages: list[AgentMessage] = chat.messages or []

    # Example AI usage
    messages = []
    with OllamaApiClient("localhost:11434", "qwen3:8b") as client:
        tools = generate_ollama_tools()
        review_agent = CodeReviewAgent(
            client,
            tools=tools,
        )
        state = ProgramState.USER_CONTROL
        while True:
            if state == ProgramState.USER_CONTROL:
                user_request = input("\nWhat should the agent review?: ")
                review_agent.add_user_message(
                    {
                        "role": "user",
                        "content": user_request,
                        "images": None,
                        "tool_calls": None,
                    }
                )

                if user_request == "exit":
                    return

            state = await review_agent.invoke()

            log.debug(messages)

            # Save conversation after each agent interaction
            # with db_manager.get_session() as session:
            #     save_messages(session, chat.id, messages)


if __name__ == "__main__":
    asyncio.run(main())
