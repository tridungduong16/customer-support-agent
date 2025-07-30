from typing import List, Optional

from pydantic import BaseModel
from pydantic import Field


class ChatRequest(BaseModel):
    question: str = Field(
        description="I bought 3 items: a jacket for $180, a pair of shoes for $120, and a backpack for $60. I received a 15% discount on the total bill and then had to pay a 10% sales tax on the discounted amount. How much do I need to pay in total?"
    )


class Message(BaseModel):
    role: str
    content: str


class UserThread(BaseModel):
    user_id: str
    thread_id: Optional[str] = "1234"
    agent_name: Optional[str] = "MISS CHINA AI"


class ConversationInfor(BaseModel):
    user_thread_infor: UserThread
    messages: List[Message]


class UserQuestion(BaseModel):
    user_thread: UserThread
    question: str
