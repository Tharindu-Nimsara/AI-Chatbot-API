from fastapi import APIRouter, HTTPException, Security
from app.models.memory import (
    HistoryResponse,
    ConversationListResponse,
    ClearHistoryResponse,
    MessageRecord,
    ConversationStats
)
from app.services.memory_service import memory_service
from app.core.security import verify_api_key
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["history"]
)


@router.get(
    "/history/{session_id}",
    response_model=HistoryResponse
)
async def get_history(
    session_id: str,
    api_key: str = Security(verify_api_key)
):
    """Get the full conversation history for a session."""
    messages = memory_service.get_history_for_display(session_id)
    stats = memory_service.get_stats(session_id)

    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"No conversation found for session: {session_id}"
        )

    return HistoryResponse(
        session_id=session_id,
        messages=[MessageRecord(**m) for m in messages],
        stats=ConversationStats(**stats)
    )


@router.get(
    "/conversations",
    response_model=ConversationListResponse
)
async def list_conversations(
    api_key: str = Security(verify_api_key)
):
    """List all conversations."""
    conversations = memory_service.get_all_conversations()

    return ConversationListResponse(
        conversations=[ConversationStats(**c) for c in conversations],
        total=len(conversations)
    )


@router.delete(
    "/history/{session_id}",
    response_model=ClearHistoryResponse
)
async def clear_history(
    session_id: str,
    api_key: str = Security(verify_api_key)
):
    """Clear all memory for a specific session."""
    success = memory_service.clear_conversation(session_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No conversation found for session: {session_id}"
        )

    return ClearHistoryResponse(
        success=True,
        message="Conversation history cleared successfully",
        session_id=session_id
    )