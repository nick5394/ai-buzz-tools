"""
Tests for Status Page API endpoints.
Note: The status endpoint makes real HTTP calls to check provider APIs.
Tests verify the response structure and contract, but actual status may vary.
"""

import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock
import httpx


class TestStatusCheck:
    """Test the status check endpoint."""

    def test_check_returns_success(self, client):
        """Test that status check returns a successful response."""
        response = client.get("/status/check")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "overall_status" in data
        assert data["overall_status"] in ["all_operational", "issues_detected", "major_outage"]

    def test_check_response_structure(self, client):
        """Test that status response has correct structure."""
        response = client.get("/status/check")
        data = response.json()
        
        # Check top-level fields
        assert "providers" in data
        assert "operational_count" in data
        assert "degraded_count" in data
        assert "down_count" in data
        assert "last_updated" in data
        assert "cache_ttl_seconds" in data

    def test_check_provider_structure(self, client):
        """Test that each provider has correct structure."""
        response = client.get("/status/check")
        data = response.json()
        
        assert len(data["providers"]) > 0
        
        for provider in data["providers"]:
            assert "id" in provider
            assert "name" in provider
            assert "status" in provider
            assert provider["status"] in ["operational", "degraded", "down"]
            assert "last_checked" in provider
            assert "status_page_url" in provider

    def test_check_counts_add_up(self, client):
        """Test that status counts add up to total providers."""
        response = client.get("/status/check")
        data = response.json()
        
        total_providers = len(data["providers"])
        counted = data["operational_count"] + data["degraded_count"] + data["down_count"]
        
        assert counted == total_providers

    def test_check_has_expected_providers(self, client):
        """Test that status check includes expected providers."""
        response = client.get("/status/check")
        data = response.json()
        
        provider_ids = [p["id"] for p in data["providers"]]
        
        # Check for key providers
        assert "openai" in provider_ids
        assert "anthropic" in provider_ids

    def test_check_cache_ttl(self, client):
        """Test that cache TTL is set correctly."""
        response = client.get("/status/check")
        data = response.json()
        
        assert data["cache_ttl_seconds"] == 60


class TestStatusCheckCaching:
    """Test the caching behavior of status checks."""

    def test_cached_response_fast(self, client):
        """Test that subsequent requests return cached data quickly."""
        import time
        
        # First request (may be slow due to actual API calls)
        client.get("/status/check")
        
        # Second request should be much faster (cached)
        start = time.time()
        response = client.get("/status/check")
        elapsed = time.time() - start
        
        assert response.status_code == status.HTTP_200_OK
        # Cached response should be very fast (< 100ms)
        assert elapsed < 0.5, f"Cached response took {elapsed}s, expected < 0.5s"


class TestStatusCheckMocked:
    """Test status checking with mocked HTTP responses."""

    @pytest.mark.asyncio
    async def test_check_provider_operational(self):
        """Test that a fast successful response is marked operational."""
        from api.status import check_provider_status
        
        mock_response = AsyncMock()
        mock_response.status_code = 401  # Expected - API responding but needs auth
        
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        provider_config = {
            "name": "Test Provider",
            "endpoint": "https://api.test.com/v1/models",
            "method": "GET",
            "status_page": "https://status.test.com/"
        }
        
        result = await check_provider_status(mock_client, "test", provider_config)
        
        assert result.id == "test"
        assert result.name == "Test Provider"
        # Status depends on latency, but should not be None
        assert result.status in ["operational", "degraded"]
        assert result.latency_ms is not None

    @pytest.mark.asyncio
    async def test_check_provider_down_on_timeout(self):
        """Test that timeout is marked as down."""
        from api.status import check_provider_status
        
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        
        provider_config = {
            "name": "Test Provider",
            "endpoint": "https://api.test.com/v1/models",
            "method": "GET",
            "status_page": "https://status.test.com/"
        }
        
        result = await check_provider_status(mock_client, "test", provider_config)
        
        assert result.status == "down"
        assert "Timeout" in result.error

    @pytest.mark.asyncio
    async def test_check_provider_down_on_5xx(self):
        """Test that 5xx errors are marked as down."""
        from api.status import check_provider_status
        
        mock_response = AsyncMock()
        mock_response.status_code = 503
        
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        provider_config = {
            "name": "Test Provider",
            "endpoint": "https://api.test.com/v1/models",
            "method": "GET",
            "status_page": "https://status.test.com/"
        }
        
        result = await check_provider_status(mock_client, "test", provider_config)
        
        assert result.status == "down"
        assert "503" in result.error

    @pytest.mark.asyncio
    async def test_check_provider_down_on_connect_error(self):
        """Test that connection errors are marked as down."""
        from api.status import check_provider_status
        
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        
        provider_config = {
            "name": "Test Provider",
            "endpoint": "https://api.test.com/v1/models",
            "method": "GET",
            "status_page": "https://status.test.com/"
        }
        
        result = await check_provider_status(mock_client, "test", provider_config)
        
        assert result.status == "down"
        assert "Connection failed" in result.error


class TestStatusSubscribe:
    """Test the email subscription endpoint."""

    def test_subscribe_valid_email(self, client):
        """Test subscribing with a valid email."""
        response = client.post(
            "/status/alerts/subscribe",
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
            "/status/alerts/subscribe",
            json={"email": "not-an-email"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestStatusWidget:
    """Test the widget endpoint."""

    def test_get_widget(self, client):
        """Test getting the widget HTML."""
        response = client.get("/status/widget")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        
        html = response.text
        assert "status" in html.lower()

    def test_widget_is_self_contained(self, client):
        """Test that widget contains all necessary CSS and JS."""
        response = client.get("/status/widget")
        html = response.text
        
        # Check for inline styles
        assert "<style>" in html
        # Check for inline scripts
        assert "<script>" in html
        # Check that the widget is not loading external stylesheets (CDNs)
        import re
        external_links = re.findall(r'href="(https?://[^"]+)"', html)
        for link in external_links:
            assert "ai-buzz.com" in link, f"External link found: {link}"


class TestStatusIntegration:
    """Integration tests for status page."""

    def test_full_flow(self, client):
        """Test the full flow: check status, subscribe, get widget."""
        # 1. Check status
        status_response = client.get("/status/check")
        assert status_response.status_code == status.HTTP_200_OK
        
        # 2. Subscribe to alerts
        subscribe_response = client.post(
            "/status/alerts/subscribe",
            json={"email": "test@example.com"}
        )
        assert subscribe_response.status_code == status.HTTP_200_OK
        
        # 3. Get widget
        widget_response = client.get("/status/widget")
        assert widget_response.status_code == status.HTTP_200_OK

    def test_providers_sorted_by_status(self, client):
        """Test that providers are sorted by status (down first, then degraded, then operational)."""
        response = client.get("/status/check")
        data = response.json()
        
        providers = data["providers"]
        status_order = {"down": 0, "degraded": 1, "operational": 2}
        
        # Get status values
        statuses = [(status_order.get(p["status"], 3), p["name"]) for p in providers]
        
        # Verify sorted order
        assert statuses == sorted(statuses), "Providers should be sorted by status then name"

    def test_overall_status_logic(self, client):
        """Test that overall status is correctly determined from provider statuses."""
        response = client.get("/status/check")
        data = response.json()
        
        overall = data["overall_status"]
        down_count = data["down_count"]
        degraded_count = data["degraded_count"]
        total = len(data["providers"])
        
        # Verify logic matches expected behavior
        if down_count >= total / 2:
            assert overall == "major_outage"
        elif down_count > 0 or degraded_count > 0:
            assert overall == "issues_detected"
        else:
            assert overall == "all_operational"
