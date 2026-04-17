import sys
import os

# Manually add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Point to a test database — never touch the real one
os.environ["DATABASE_URL"] = "data/test_chatbot.db"
os.environ["API_SECRET_KEY"] = "test-secret-key"
os.environ["GITHUB_TOKEN"] = "fake-token-for-testing"

from app.main import app
from app.core.database import initialize_database


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Create a fresh test database before the test session.
    Runs once for all tests.
    """
    initialize_database()
    yield
    # Cleanup test database after all tests finish
    if os.path.exists("data/test_chatbot.db"):
        os.remove("data/test_chatbot.db")


@pytest.fixture
def client():
    """
    HTTP test client — simulates real HTTP requests
    without starting a real server.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers():
    """Valid auth headers for protected endpoints."""
    return {"X-API-Key": "test-secret-key"}


@pytest.fixture
def mock_llm_response():
    """
    Fake LLM response — prevents real API calls during tests.
    Tests should NEVER call paid external APIs.
    """
    mock = MagicMock()
    mock.choices[0].message.content = "This is a test response from the AI."
    mock.usage.prompt_tokens = 50
    mock.usage.completion_tokens = 20
    mock.model = "microsoft/Phi-4"
    return mock