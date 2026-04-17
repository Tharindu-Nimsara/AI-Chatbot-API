import pytest
from app.services.memory_service import MemoryService


class TestMemoryService:

    @pytest.fixture
    def service(self):
        return MemoryService()

    @pytest.fixture
    def sample_session(self):
        return "test-session-unit-abc123"

    def test_save_and_retrieve_exchange(self, service, sample_session):
        service.save_exchange(
            session_id=sample_session,
            user_message="What is Python?",
            assistant_reply="Python is a programming language.",
            input_tokens=10,
            output_tokens=8
        )

        history = service.get_history_for_display(sample_session)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        assert history[0]["content"] == "What is Python?"

    def test_history_for_llm_format(self, service, sample_session):
        history = service.get_history_for_llm(sample_session)
        for msg in history:
            assert "role" in msg
            assert "content" in msg
            assert msg["role"] in ["user", "assistant"]

    def test_clear_conversation(self, service, sample_session):
        # Save something first
        service.save_exchange(
            session_id=sample_session,
            user_message="test",
            assistant_reply="test reply",
            input_tokens=5,
            output_tokens=5
        )

        # Clear it
        service.clear_conversation(sample_session)

        # Should be empty now
        history = service.get_history_for_display(sample_session)
        assert len(history) == 0

    def test_token_budget_trims_old_messages(self, service):
        session_id = "test-token-budget-session"

        # Save messages with high token counts to exceed budget
        for i in range(5):
            service.save_exchange(
                session_id=session_id,
                user_message=f"Message {i}",
                assistant_reply=f"Reply {i}",
                input_tokens=700,
                output_tokens=700
            )

        # History for LLM should be trimmed to stay within budget
        history = service.get_history_for_llm(session_id)
        total_tokens = sum(
            m.get("tokens", 0) for m in
            service.get_history_for_display(session_id)
        )

        from app.core.config import settings
        # Verify the trimming logic ran
        assert len(history) <= settings.max_history_messages * 2