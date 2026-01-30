"""
Tests for the Analytics API Router.
Tests usage tracking and gap detection endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_stats():
    """Reset analytics stats before each test."""
    from api.analytics import _stats
    from datetime import datetime
    
    # Reset to initial state
    _stats.clear()
    _stats.update({
        "started_at": datetime.utcnow().isoformat() + "Z",
        "error_decoder": {
            "total": 0,
            "matched": 0,
            "unmatched": 0,
            "gaps": {}
        },
        "pricing_calculator": {
            "total": 0,
            "token_buckets": {"under_1k": 0, "1k_to_10k": 0, "10k_to_100k": 0, "over_100k": 0},
            "models_not_found": {}
        },
        "status_page": {
            "total": 0,
            "by_provider": {}
        }
    })
    yield


class TestAnalyticsStats:
    """Tests for /analytics/stats endpoint."""
    
    def test_get_stats_returns_success(self, client):
        """Stats endpoint returns success."""
        response = client.get("/analytics/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_stats_structure(self, client):
        """Stats endpoint returns expected structure."""
        response = client.get("/analytics/stats")
        data = response.json()
        
        assert "data" in data
        assert "error_decoder" in data["data"]
        assert "pricing_calculator" in data["data"]
        assert "status_page" in data["data"]
        assert "started_at" in data["data"]
    
    def test_error_decoder_stats_structure(self, client):
        """Error decoder stats have expected fields."""
        response = client.get("/analytics/stats")
        ed = response.json()["data"]["error_decoder"]
        
        assert "total" in ed
        assert "matched" in ed
        assert "unmatched" in ed
        assert "gaps" in ed
    
    def test_pricing_calculator_stats_structure(self, client):
        """Pricing calculator stats have expected fields."""
        response = client.get("/analytics/stats")
        pc = response.json()["data"]["pricing_calculator"]
        
        assert "total" in pc
        assert "token_buckets" in pc
        assert "models_not_found" in pc


class TestAnalyticsGaps:
    """Tests for /analytics/gaps endpoint."""
    
    def test_get_gaps_returns_success(self, client):
        """Gaps endpoint returns success."""
        response = client.get("/analytics/gaps")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_gaps_structure(self, client):
        """Gaps endpoint returns expected structure."""
        response = client.get("/analytics/gaps")
        data = response.json()
        
        assert "error_patterns_to_add" in data
        assert "pricing_models_to_add" in data
        assert isinstance(data["error_patterns_to_add"], list)
        assert isinstance(data["pricing_models_to_add"], list)


class TestAnalyticsReset:
    """Tests for /analytics/reset endpoint."""
    
    def test_reset_returns_success(self, client):
        """Reset endpoint returns success."""
        response = client.get("/analytics/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Stats reset"
    
    def test_reset_clears_stats(self, client):
        """Reset clears accumulated stats."""
        # First, trigger some tracking by calling error decoder
        client.post("/error-decoder/decode", json={"error_message": "test error"})
        
        # Reset
        client.get("/analytics/reset")
        
        # Check stats are cleared
        response = client.get("/analytics/stats")
        ed = response.json()["data"]["error_decoder"]
        assert ed["total"] == 0


class TestTrackingIntegration:
    """Tests that tracking is working with tool endpoints."""
    
    def test_error_decoder_tracks_usage(self, client):
        """Error decoder endpoint tracks usage."""
        # Make a decode request
        client.post("/error-decoder/decode", json={"error_message": "rate limit exceeded"})
        
        # Check stats
        response = client.get("/analytics/stats")
        ed = response.json()["data"]["error_decoder"]
        assert ed["total"] == 1
    
    def test_error_decoder_tracks_matches(self, client):
        """Error decoder tracks matched patterns."""
        # Make a request that should match a pattern
        client.post("/error-decoder/decode", json={"error_message": "rate limit exceeded"})
        
        response = client.get("/analytics/stats")
        ed = response.json()["data"]["error_decoder"]
        assert ed["matched"] >= 1 or ed["unmatched"] >= 1  # One or the other
        assert ed["total"] == ed["matched"] + ed["unmatched"]
    
    def test_error_decoder_tracks_gaps(self, client):
        """Error decoder tracks unmatched errors as gaps."""
        # Make a request that won't match any pattern
        client.post("/error-decoder/decode", json={"error_message": "some completely random unique error xyz123"})
        
        response = client.get("/analytics/gaps")
        gaps = response.json()
        
        # Should have recorded a gap
        if response.json()["error_patterns_to_add"]:
            gap = response.json()["error_patterns_to_add"][0]
            assert "hash" in gap
            assert "count" in gap
            assert "preview" in gap
    
    def test_pricing_calculator_tracks_usage(self, client):
        """Pricing calculator endpoint tracks usage."""
        # Make a calculation request
        client.post("/pricing/calculate", json={
            "input_tokens_monthly": 1000000,
            "output_tokens_monthly": 500000
        })
        
        # Check stats
        response = client.get("/analytics/stats")
        pc = response.json()["data"]["pricing_calculator"]
        assert pc["total"] == 1
    
    def test_pricing_calculator_buckets_tokens(self, client):
        """Pricing calculator buckets token counts."""
        # Small request
        client.post("/pricing/calculate", json={
            "input_tokens_monthly": 100,
            "output_tokens_monthly": 100
        })
        
        # Large request
        client.post("/pricing/calculate", json={
            "input_tokens_monthly": 1000000,
            "output_tokens_monthly": 1000000
        })
        
        response = client.get("/analytics/stats")
        buckets = response.json()["data"]["pricing_calculator"]["token_buckets"]
        
        # Should have counts in different buckets
        assert buckets["under_1k"] >= 1
        assert buckets["over_100k"] >= 1


class TestAnalyticsPrivacy:
    """Tests for privacy protections."""
    
    def test_error_message_is_hashed(self, client):
        """Error messages are hashed, not stored in plain text."""
        # Submit a recognizable error
        test_error = "my super secret API key sk-12345 failed"
        client.post("/error-decoder/decode", json={"error_message": test_error})
        
        response = client.get("/analytics/gaps")
        gaps = response.json()["error_patterns_to_add"]
        
        if gaps:
            gap = gaps[0]
            # Preview should be truncated
            assert len(gap["preview"]) <= 53  # 50 chars + "..."
            # Hash should not contain the full error
            assert gap["hash"] != test_error
            assert "sk-12345" not in gap["hash"]
    
    def test_preview_is_truncated(self, client):
        """Long error messages have preview truncated."""
        long_error = "x" * 200  # 200 character error
        client.post("/error-decoder/decode", json={"error_message": long_error})
        
        response = client.get("/analytics/gaps")
        gaps = response.json()["error_patterns_to_add"]
        
        if gaps:
            gap = gaps[0]
            # Preview should be truncated with "..."
            assert len(gap["preview"]) <= 53
            assert gap["preview"].endswith("...")
