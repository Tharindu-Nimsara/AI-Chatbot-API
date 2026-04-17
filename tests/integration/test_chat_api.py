import pytest
from unittest.mock import patch, MagicMock


class TestChatEndpoint:

    def test_chat_without_api_key_returns_401(self, client):
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hello"}
        )
        assert response.status_code == 401

    def test_chat_with_wrong_api_key_returns_401(self, client):
        response = client.post(
            "/api/v1/chat",
            headers={"X-API-Key": "wrong-key"},
            json={"message": "Hello"}
        )
        assert response.status_code == 401

    def test_chat_with_empty_message_returns_422(self, client, auth_headers):
        response = client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json={"message": ""}
        )
        assert response.status_code in [400, 422]

    def test_chat_success_returns_correct_shape(
        self, client, auth_headers, mock_llm_response
    ):
        with patch(
            "app.services.llm_service.LLMService.__init__",
            return_value=None
        ):
            with patch(
                "app.services.llm_service.llm_service.chat"
            ) as mock_chat:
                mock_chat.return_value = {
                    "reply": "This is a test response.",
                    "session_id": "test-session-123",
                    "model": "microsoft/Phi-4",
                    "input_tokens": 50,
                    "output_tokens": 20
                }

                response = client.post(
                    "/api/v1/chat",
                    headers=auth_headers,
                    json={"message": "Hello Aria!"}
                )

        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "session_id" in data
        assert "model" in data
        assert "input_tokens" in data
        assert "output_tokens" in data

    def test_chat_returns_session_id(
        self, client, auth_headers
    ):
        with patch(
            "app.services.llm_service.llm_service.chat"
        ) as mock_chat:
            mock_chat.return_value = {
                "reply": "Hello!",
                "session_id": "generated-session-id",
                "model": "microsoft/Phi-4",
                "input_tokens": 30,
                "output_tokens": 10
            }

            response = client.post(
                "/api/v1/chat",
                headers=auth_headers,
                json={"message": "Hi"}
            )

        assert response.status_code == 200
        assert response.json()["session_id"] is not None

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"