"""
Pytest configuration and shared fixtures for AI-Buzz Tools tests.
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_error_message():
    """Sample error message for testing."""
    return "rate limit exceeded. Please try again in 10 seconds"


@pytest.fixture
def sample_openai_error():
    """Sample OpenAI error message."""
    return "Rate limit exceeded. You have exceeded your rate limit. Please try again later."


@pytest.fixture
def sample_anthropic_error():
    """Sample Anthropic error message."""
    return "authentication failed: invalid api key"


@pytest.fixture
def sample_unknown_error():
    """Sample error that doesn't match any pattern."""
    return "Some random error message that doesn't match any known pattern"
