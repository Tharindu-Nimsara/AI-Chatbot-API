import pytest
from app.services.memory_service import memory_service


class TestHistoryEndpoint:

    @pytest.fixture
    def seeded_session(self):
        """Create a session with real data in the test DB."""
        session_id = "integration-test-session-xyz"
        memory_service.save_exchange(
            session_id=session_id,
            user_message="What is FastAPI?",
            assistant_reply="FastAPI is a modern Python web framework.",
            input_tokens=15,
            output_tokens=10
        )
        return session_id

    def test_get_history_without_auth_returns_401(self, client):
        response = client.get("/api/v1/history/some-session")
        assert response.status_code == 401

    def test_get_history_not_found_returns_404(self, client, auth_headers):
        response = client.get(
            "/api/v1/history/nonexistent-session-id",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_get_history_returns_messages(
        self, client, auth_headers, seeded_session
    ):
        response = client.get(
            f"/api/v1/history/{seeded_session}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "stats" in data
        assert len(data["messages"]) >= 2

    def test_list_conversations(self, client, auth_headers, seeded_session):
        response = client.get(
            "/api/v1/conversations",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_clear_history(self, client, auth_headers, seeded_session):
        response = client.delete(
            f"/api/v1/history/{seeded_session}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["success"] is True