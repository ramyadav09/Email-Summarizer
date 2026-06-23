from pydantic import BaseModel
from typing import Optional


class SummarizeRequest(BaseModel):
    id: str
    body: Optional[str] = None


class SummarizeResponse(BaseModel):
    summary: str


class GenerateReplyRequest(BaseModel):
    id: str
    from_addr: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None


class GenerateReplyResponse(BaseModel):
    reply: str


class SendReplyRequest(BaseModel):
    id: str
    thread_id: str
    to: str
    subject: str
    body: str
    message_id: str = ""


class SendReplyResponse(BaseModel):
    messageId: str
    threadId: str

