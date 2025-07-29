import asyncio
import json
from markdown import markdown
from src.agents.builder import build_graph
from src.database_handler.mongodb_handler import MemoryHandler
from src.schema import ConversationInfor, Message, UserQuestion, UserThread


class AgentManager:
    def __init__(self):
        self.graph = build_graph()
        self.memory_handler = MemoryHandler()

    def _save_conversation(self, user_thread: UserThread, question: str, answer: str):
        conversation = ConversationInfor(
            user_thread_infor=user_thread,
            messages=[
                Message(role="user", content=question),
                Message(role="assistant", content=answer),
            ],
        )
        self.memory_handler.insert_or_update_conversation(conversation)

    def _get_chat_history(self, user_thread: UserThread):
        chat_history = self.memory_handler.retrieve_conversation(user_thread)
        if not chat_history or "messages" not in chat_history:
            return []
        messages = chat_history["messages"]
        return [
            {"role": msg["role"], "content": msg["content"]} for msg in messages[-6:]
        ]

    def process_question_stream(self, user_question, agent):
        messages = self._get_chat_history(user_question.user_thread)
        messages.append({"role": "user", "content": user_question.question})
        inputs = {
            "messages": messages,
        }
        for s in agent.stream(inputs, stream_mode="values"):
            message = s["messages"][-1]
            print(message.content)


if __name__ == "__main__":
    call_agent = AgentManager()
    question = "The total is $50 with a 10 percent discount. How much do I need to pay?"
    user_thread = UserThread(user_id="123", thread_id="456")
    user_question = UserQuestion(user_thread=user_thread, question=question)
    call_agent.process_question_stream(user_question, call_agent.graph)
