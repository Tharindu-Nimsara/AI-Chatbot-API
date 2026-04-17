import os
import sys

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock


PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# Point test runs at an isolated database before importing app modules.
os.environ.setdefault("DATABASE_URL", "data/test_chatbot.db")
os.environ.setdefault("API_SECRET_KEY", "test-secret-key")
os.environ.setdefault("GITHUB_TOKEN", "fake-token-for-testing")


from app.main import app
from app.core.database import initialize_database


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create a fresh test database before the test session."""
    initialize_database()
    yield
    if os.path.exists("data/test_chatbot.db"):
        os.remove("data/test_chatbot.db")


@pytest.fixture
def client():
    """HTTP test client for API tests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers():
    return {"X-API-Key": "test-secret-key"}


@pytest.fixture
def mock_llm_response():
    mock = MagicMock()
    mock.choices[0].message.content = "This is a test response from the AI."
    mock.usage.prompt_tokens = 50
    mock.usage.completion_tokens = 20
    mock.model = "microsoft/Phi-4"
    return mock