from pydantic import BaseModel
from typing import Optional


class MessageRecord(BaseModel):
    role: str
    content: str
    tokens: int
    created_at: str


class ConversationStats(BaseModel):
    session_id: str
    created_at: str
    updated_at: str
    message_count: int
    total_tokens: int


class HistoryResponse(BaseModel):
    session_id: str
    messages: list[MessageRecord]
    stats: ConversationStats


class ConversationListResponse(BaseModel):
    conversations: list[ConversationStats]
    total: int


class ClearHistoryResponse(BaseModel):
    success: bool
    message: str
    session_id: str