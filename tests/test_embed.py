"""
Tests for Embed API endpoints.
"""

import pytest
from fastapi import status


class TestEmbedScript:
    """Test the embed.js endpoint."""

    def test_get_embed_script(self, client):
        """Test that embed.js serves correctly."""
        response = client.get("/embed.js")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/javascript"
        
        # Check that the script contains expected code
        content = response.text
        assert "AI-Buzz embed" in content
        assert "data-tool" in content
        assert "fetch" in content
        assert "pricing" in content
        assert "status" in content
        assert "error-decoder" in content

    def test_embed_script_has_cache_headers(self, client):
        """Test that embed.js has appropriate cache headers."""
        response = client.get("/embed.js")
        
        assert response.status_code == status.HTTP_200_OK
        assert "Cache-Control" in response.headers
        assert "public" in response.headers["Cache-Control"]

    def test_embed_script_contains_tool_endpoints(self, client):
        """Test that embed.js contains all tool endpoint mappings."""
        response = client.get("/embed.js")
        
        assert response.status_code == status.HTTP_200_OK
        content = response.text
        
        # Check that all tool endpoints are present
        assert "/pricing/widget" in content
        assert "/status/widget" in content
        assert "/error-decoder/widget" in content

    def test_embed_script_has_retry_logic(self, client):
        """Test that embed.js includes retry logic for cold starts."""
        response = client.get("/embed.js")
        
        assert response.status_code == status.HTTP_200_OK
        content = response.text
        
        # Check for retry logic
        assert "retryCount" in content or "retry" in content.lower()
        assert "setTimeout" in content
