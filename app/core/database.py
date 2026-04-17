import sqlite3
import os
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    """
    Create and return a SQLite database connection.
    Each call gets a fresh connection — SQLite handles this efficiently.
    """
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(settings.database_url), exist_ok=True)

    conn = sqlite3.connect(
        settings.database_url,
        check_same_thread=False    # Required for FastAPI's async threads
    )

    # Return rows as dictionaries instead of tuples
    conn.row_factory = sqlite3.Row

    return conn


def initialize_database():
    """
    Create all tables if they don't exist.
    Called once on app startup.
    """
    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Conversations table — one row per session
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                session_id      TEXT PRIMARY KEY,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count   INTEGER DEFAULT 0,
                total_tokens    INTEGER DEFAULT 0
            )
        """)

        # Messages table — every user + assistant message
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id      TEXT NOT NULL,
                role            TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content         TEXT NOT NULL,
                tokens          INTEGER DEFAULT 0,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES conversations(session_id)
            )
        """)

        # Index for fast history lookup by session
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session
            ON messages(session_id, created_at)
        """)

        conn.commit()
        logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

    finally:
        conn.close()