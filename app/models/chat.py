from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's message to the chatbot"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for conversation tracking"
    )


class ChatResponse(BaseModel):
    reply: str = Field(description="The AI's response")
    session_id: str = Field(description="Session ID for this conversation")
    model: str = Field(description="The LLM model used")
    input_tokens: int = Field(description="Tokens used in the prompt")
    output_tokens: int = Field(description="Tokens used in the response")


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None