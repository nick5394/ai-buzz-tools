"""
Tests for Error Decoder API endpoints.
"""

import pytest
from fastapi import status


class TestErrorDecoderDecode:
    """Test the error decoding endpoint."""

    def test_decode_rate_limit_error(self, client, sample_error_message):
        """Test decoding a rate limit error."""
        response = client.post(
            "/error-decoder/decode",
            json={"error_message": sample_error_message}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["error_message"] == sample_error_message
        assert data["decoded"] is not None
        assert data["decoded"]["pattern"]["provider_id"] in ["openai", "anthropic", "common"]
        assert "rate limit" in data["decoded"]["pattern"]["title"].lower()
        assert data["decoded"]["confidence"] in ["high", "medium", "low"]
        assert len(data["decoded"]["matched_keywords"]) > 0

    def test_decode_openai_auth_error(self, client, sample_openai_error):
        """Test decoding an OpenAI authentication error."""
        response = client.post(
            "/error-decoder/decode",
            json={"error_message": "invalid api key"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["decoded"] is not None
        assert "auth" in data["decoded"]["pattern"]["title"].lower() or "api key" in data["decoded"]["pattern"]["title"].lower()

    def test_decode_unknown_error(self, client, sample_unknown_error):
        """Test decoding an unknown error returns suggestions."""
        response = client.post(
            "/error-decoder/decode",
            json={"error_message": sample_unknown_error}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["decoded"] is None
        assert len(data["suggestions"]) > 0

    def test_decode_empty_error(self, client):
        """Test decoding with empty error message."""
        response = client.post(
            "/error-decoder/decode",
            json={"error_message": ""}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_decode_get_version(self, client, sample_error_message):
        """Test GET version of decode endpoint for shareable URLs."""
        response = client.get(
            "/error-decoder/decode",
            params={"error_message": sample_error_message}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True


class TestErrorDecoderPatterns:
    """Test the patterns listing endpoint."""

    def test_get_all_patterns(self, client):
        """Test getting all error patterns."""
        response = client.get("/error-decoder/patterns")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert len(data["patterns"]) > 0
        assert len(data["providers"]) > 0
        
        # Check pattern structure
        pattern = data["patterns"][0]
        assert "id" in pattern
        assert "provider" in pattern
        assert "provider_id" in pattern
        assert "error_keywords" in pattern
        assert "title" in pattern
        assert "explanation" in pattern
        assert "fix" in pattern
        assert "severity" in pattern
        assert pattern["severity"] in ["error", "warning"]

    def test_patterns_have_required_fields(self, client):
        """Test that all patterns have required fields."""
        response = client.get("/error-decoder/patterns")
        data = response.json()
        
        required_fields = [
            "id", "provider", "provider_id", "error_keywords",
            "title", "explanation", "fix", "severity", "common"
        ]
        
        for pattern in data["patterns"]:
            for field in required_fields:
                assert field in pattern, f"Pattern {pattern.get('id')} missing field: {field}"


class TestErrorDecoderSubscribe:
    """Test the email subscription endpoint."""

    def test_subscribe_valid_email(self, client):
        """Test subscribing with a valid email."""
        response = client.post(
            "/error-decoder/alerts/subscribe",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "message" in data
        assert "mailchimp_synced" in data

    def test_subscribe_invalid_email(self, client):
        """Test subscribing with an invalid email."""
        response = client.post(
            "/error-decoder/alerts/subscribe",
            json={"email": "not-an-email"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestErrorDecoderWidget:
    """Test the widget endpoint."""

    def test_get_widget(self, client):
        """Test getting the widget HTML."""
        response = client.get("/error-decoder/widget")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        
        html = response.text
        assert "error-decoder-widget" in html
        assert "Decode Error" in html
        assert "Paste Your Error Message" in html

    def test_widget_is_self_contained(self, client):
        """Test that widget contains all necessary CSS and JS."""
        response = client.get("/error-decoder/widget")
        html = response.text
        
        # Check for inline styles
        assert "<style>" in html
        # Check for inline scripts
        assert "<script>" in html
        # Check that the widget is not loading external stylesheets (CDNs)
        # Share URLs to ai-buzz.com are allowed, mailto links are allowed
        import re
        external_links = re.findall(r'href="(https?://[^"]+)"', html)
        for link in external_links:
            assert "ai-buzz.com" in link, f"External link found: {link}"

    def test_widget_has_feedback_mailto_link(self, client):
        """Test that widget has a feedback mailto link with correct format."""
        response = client.get("/error-decoder/widget")
        html = response.text
        
        # Check for feedback mailto link
        assert 'mailto:aibuzzofficial@gmail.com' in html
        assert 'Send Feedback' in html
        assert 'edw-feedback-link' in html
        # Check subject contains tool name
        assert 'Error%20Decoder' in html or 'Error+Decoder' in html


class TestErrorDecoderIntegration:
    """Integration tests for error decoder."""

    def test_full_flow(self, client):
        """Test the full flow: decode error, get patterns, subscribe."""
        # 1. Decode an error
        decode_response = client.post(
            "/error-decoder/decode",
            json={"error_message": "rate limit exceeded"}
        )
        assert decode_response.status_code == status.HTTP_200_OK
        
        # 2. Get all patterns
        patterns_response = client.get("/error-decoder/patterns")
        assert patterns_response.status_code == status.HTTP_200_OK
        
        # 3. Subscribe to alerts
        subscribe_response = client.post(
            "/error-decoder/alerts/subscribe",
            json={"email": "test@example.com"}
        )
        assert subscribe_response.status_code == status.HTTP_200_OK
        
        # 4. Get widget
        widget_response = client.get("/error-decoder/widget")
        assert widget_response.status_code == status.HTTP_200_OK
