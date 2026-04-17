import logging
from app.repositories.memory_repository import memory_repository
from app.core.config import settings

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Manages conversation memory with context window awareness.
    Sits between the repository (raw DB) and the LLM service (API calls).
    """

    def save_exchange(
        self,
        session_id: str,
        user_message: str,
        assistant_reply: str,
        input_tokens: int,
        output_tokens: int
    ):
        """
        Save a full user/assistant exchange to memory.
        Called after every successful LLM response.
        """
        # Ensure conversation record exists
        memory_repository.create_or_update_conversation(session_id)

        # Save user message
        memory_repository.save_message(
            session_id=session_id,
            role="user",
            content=user_message,
            tokens=input_tokens
        )

        # Save assistant reply
        memory_repository.save_message(
            session_id=session_id,
            role="assistant",
            content=assistant_reply,
            tokens=output_tokens
        )

        logger.info(
            f"Exchange saved | session: {session_id} | "
            f"tokens: {input_tokens + output_tokens}"
        )

    def get_history_for_llm(self, session_id: str) -> list[dict]:
        """
        Retrieve conversation history formatted for the LLM API.
        Applies context window limits to stay within token budget.
        """
        messages = memory_repository.get_messages(
            session_id=session_id,
            limit=settings.max_history_messages
        )

        if not messages:
            return []

        # Apply token budget — trim oldest messages if over limit
        filtered = self._apply_token_budget(messages)

        # Format for LLM API
        llm_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in filtered
        ]

        logger.info(
            f"History loaded | session: {session_id} | "
            f"{len(llm_messages)} messages"
        )

        return llm_messages

    def _apply_token_budget(self, messages: list[dict]) -> list[dict]:
        """
        Trim messages from the oldest end if total tokens
        exceed our budget. Always keep the most recent messages.
        """
        total_tokens = sum(m.get("tokens", 0) for m in messages)

        if total_tokens <= settings.max_history_tokens:
            return messages

        # Remove oldest messages until under budget
        while messages and total_tokens > settings.max_history_tokens:
            removed = messages.pop(0)
            total_tokens -= removed.get("tokens", 0)
            logger.debug(f"Trimmed old message | tokens remaining: {total_tokens}")

        return messages

    def get_history_for_display(self, session_id: str) -> list[dict]:
        """Get full history for the /history endpoint display."""
        return memory_repository.get_messages(
            session_id=session_id,
            limit=100    # Return more for display than for LLM
        )

    def get_stats(self, session_id: str):
        """Get conversation statistics."""
        return memory_repository.get_conversation_stats(session_id)

    def clear_conversation(self, session_id: str) -> bool:
        """Delete all memory for a session."""
        return memory_repository.delete_conversation(session_id)

    def get_all_conversations(self) -> list[dict]:
        """Get all conversations."""
        return memory_repository.get_all_conversations()


# Singleton instance
memory_service = MemoryService()