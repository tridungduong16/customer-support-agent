from typing import List, Optional

from pydantic import BaseModel


class ForkliftProduct(BaseModel):
    product_id: str
    load_capacity: Optional[float] = None
    load_center: Optional[float] = None
    wheelbase: Optional[float] = None
    height_mast_lowered: Optional[float] = None
    height_mast_extended: Optional[float] = None
    height_overhead_guard: Optional[float] = None
    height_of_seat: Optional[float] = None
    free_lift: Optional[float] = None
    lift: Optional[float] = None
    length_to_forkface: Optional[float] = None
    overall_width: Optional[float] = None
    turning_radius: Optional[float] = None


class ListForkliftProduct(BaseModel):
    products: List[ForkliftProduct]


class PdfParserRequest(BaseModel):
    pdf_path: str


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


class ChatRequest(BaseModel):
    question: str
