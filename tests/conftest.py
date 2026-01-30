"""
Pytest configuration and shared fixtures for AI-Buzz Tools tests.
"""

import pytest
import subprocess
import asyncio
import time
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


# Playwright fixtures for widget integration tests
try:
    from playwright.async_api import async_playwright, Browser, Page
    
    @pytest.fixture
    async def browser():
        """Create a Playwright browser instance for widget tests."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            yield browser
            await browser.close()
    
    @pytest.fixture
    async def page(browser):
        """Create a new Playwright page for each test."""
        page = await browser.new_page()
        # Set default timeout to 30 seconds (Playwright default - safer for CI)
        page.set_default_timeout(30000)
        yield page
        await page.close()
    
    @pytest.fixture(scope="session")
    def test_server():
        """Start FastAPI test server for widget integration tests."""
        import os
        
        # Use a different port to avoid conflicts
        port = 8765
        server_url = f"http://localhost:{port}"
        
        # Start server process
        process = subprocess.Popen(
            ["uvicorn", "main:app", "--port", str(port), "--host", "127.0.0.1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )
        
        # Wait for server to start (faster polling: 200ms instead of 1s)
        max_wait = 10
        for i in range(max_wait * 5):  # Poll every 200ms
            try:
                import urllib.request
                response = urllib.request.urlopen(f"{server_url}/", timeout=1)
                if response.getcode() == 200:
                    break
            except Exception:
                time.sleep(0.2)  # 200ms instead of 1s
        else:
            process.terminate()
            raise RuntimeError("Test server failed to start")
        
        yield server_url
        
        # Cleanup
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
    
except ImportError:
    # Playwright not available - skip widget integration tests
    @pytest.fixture
    async def browser():
        pytest.skip("Playwright not installed - skipping widget integration tests")
    
    @pytest.fixture
    async def page():
        pytest.skip("Playwright not installed - skipping widget integration tests")
    
    @pytest.fixture(scope="session")
    def test_server():
        pytest.skip("Playwright not installed - skipping widget integration tests")
