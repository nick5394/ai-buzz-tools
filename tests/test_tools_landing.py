"""
Tests for Tools Landing API endpoints.
"""

import pytest
from fastapi import status


class TestToolsLandingSubscribe:
    """Test the email subscription endpoint."""

    def test_subscribe_valid_email(self, client):
        """Test subscribing with a valid email."""
        response = client.post(
            "/tools/alerts/subscribe",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "message" in data
        assert "mailchimp_synced" in data
        assert "new tools" in data["message"].lower()

    def test_subscribe_invalid_email(self, client):
        """Test subscribing with an invalid email."""
        response = client.post(
            "/tools/alerts/subscribe",
            json={"email": "not-an-email"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_subscribe_missing_email(self, client):
        """Test subscribing without providing email."""
        response = client.post(
            "/tools/alerts/subscribe",
            json={}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestToolsLandingWidget:
    """Test the widget endpoint."""

    def test_get_widget(self, client):
        """Test getting the widget HTML."""
        response = client.get("/tools/widget")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        
        html = response.text
        assert "tools-landing" in html.lower() or "tool" in html.lower()

    def test_widget_is_self_contained(self, client):
        """Test that widget contains all necessary CSS and JS."""
        response = client.get("/tools/widget")
        html = response.text
        
        # Check for inline styles
        assert "<style>" in html
        # Check for inline scripts
        assert "<script>" in html
        # Check that the widget is not loading external stylesheets (CDNs)
        # Share URLs to ai-buzz.com are allowed
        import re
        external_links = re.findall(r'href="(https?://[^"]+)"', html)
        for link in external_links:
            assert "ai-buzz.com" in link, f"External link found: {link}"


class TestToolsLandingIntegration:
    """Integration tests for tools landing."""

    def test_full_flow(self, client):
        """Test the full flow: subscribe and get widget."""
        # 1. Subscribe to alerts
        subscribe_response = client.post(
            "/tools/alerts/subscribe",
            json={"email": "test@example.com"}
        )
        assert subscribe_response.status_code == status.HTTP_200_OK
        data = subscribe_response.json()
        assert data["success"] is True
        
        # 2. Get widget
        widget_response = client.get("/tools/widget")
        assert widget_response.status_code == status.HTTP_200_OK
        assert "text/html" in widget_response.headers["content-type"]
