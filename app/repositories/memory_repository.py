import logging
from typing import Optional
from app.core.database import get_connection

logger = logging.getLogger(__name__)


class MemoryRepository:
    """
    Handles all direct database operations for conversation memory.
    No business logic here — just clean read/write operations.
    """

    def create_or_update_conversation(self, session_id: str):
        """Create a new conversation or update its timestamp."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (session_id)
                VALUES (?)
                ON CONFLICT(session_id) DO UPDATE SET
                    updated_at = CURRENT_TIMESTAMP
            """, (session_id,))
            conn.commit()
        finally:
            conn.close()

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tokens: int = 0
    ):
        """Save a single message to the database."""
        conn = get_connection()
        try:
            cursor = conn.cursor()

            # Save the message
            cursor.execute("""
                INSERT INTO messages (session_id, role, content, tokens)
                VALUES (?, ?, ?, ?)
            """, (session_id, role, content, tokens))

            # Update conversation stats
            cursor.execute("""
                UPDATE conversations
                SET message_count = message_count + 1,
                    total_tokens  = total_tokens + ?,
                    updated_at    = CURRENT_TIMESTAMP
                WHERE session_id = ?
            """, (tokens, session_id))

            conn.commit()
            logger.debug(f"Saved {role} message | session: {session_id}")

        finally:
            conn.close()

    def get_messages(
        self,
        session_id: str,
        limit: int = 10
    ) -> list[dict]:
        """
        Retrieve the most recent N messages for a session.
        Returns in chronological order (oldest first).
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()

            # Get last N messages, then reverse to chronological order
            cursor.execute("""
                SELECT role, content, tokens, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (session_id, limit))

            rows = cursor.fetchall()

            # Reverse so oldest message comes first
            messages = [dict(row) for row in reversed(rows)]
            return messages

        finally:
            conn.close()

    def get_conversation_stats(self, session_id: str) -> Optional[dict]:
        """Get stats for a conversation."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, created_at, updated_at,
                       message_count, total_tokens
                FROM conversations
                WHERE session_id = ?
            """, (session_id,))

            row = cursor.fetchone()
            return dict(row) if row else None

        finally:
            conn.close()

    def get_all_conversations(self) -> list[dict]:
        """Get all conversations ordered by most recent."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, created_at, updated_at,
                       message_count, total_tokens
                FROM conversations
                ORDER BY updated_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def delete_conversation(self, session_id: str) -> bool:
        """Delete a conversation and all its messages."""
        conn = get_connection()
        try:
            cursor = conn.cursor()

            # Delete messages first (foreign key constraint)
            cursor.execute(
                "DELETE FROM messages WHERE session_id = ?",
                (session_id,)
            )
            cursor.execute(
                "DELETE FROM conversations WHERE session_id = ?",
                (session_id,)
            )

            conn.commit()
            deleted = cursor.rowcount > 0
            logger.info(f"Conversation deleted | session: {session_id}")
            return deleted

        finally:
            conn.close()


# Singleton instance
memory_repository = MemoryRepository()