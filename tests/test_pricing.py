"""
Tests for Pricing Calculator API endpoints.
"""

import pytest
from fastapi import status


class TestPricingModels:
    """Test the models listing endpoint."""

    def test_get_all_models(self, client):
        """Test getting all AI models with pricing."""
        response = client.get("/pricing/models")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "last_updated" in data
        assert len(data["providers"]) > 0
        
        # Check that key providers exist
        assert "openai" in data["providers"]
        assert "anthropic" in data["providers"]

    def test_models_have_required_fields(self, client):
        """Test that all models have required fields."""
        response = client.get("/pricing/models")
        data = response.json()
        
        for provider_id, provider_data in data["providers"].items():
            assert "name" in provider_data, f"Provider {provider_id} missing name"
            assert "models" in provider_data, f"Provider {provider_id} missing models"
            
            for model_id, model_data in provider_data["models"].items():
                assert "name" in model_data, f"Model {model_id} missing name"
                assert "input_per_1m" in model_data, f"Model {model_id} missing input_per_1m"
                assert "output_per_1m" in model_data, f"Model {model_id} missing output_per_1m"
                assert "context_window" in model_data, f"Model {model_id} missing context_window"
                assert "notes" in model_data, f"Model {model_id} missing notes"

    def test_pricing_values_are_positive(self, client):
        """Test that all pricing values are non-negative."""
        response = client.get("/pricing/models")
        data = response.json()
        
        for provider_id, provider_data in data["providers"].items():
            for model_id, model_data in provider_data["models"].items():
                assert model_data["input_per_1m"] >= 0, f"Model {model_id} has negative input price"
                assert model_data["output_per_1m"] >= 0, f"Model {model_id} has negative output price"
                assert model_data["context_window"] > 0, f"Model {model_id} has invalid context window"


class TestPricingCalculate:
    """Test the cost calculation endpoint."""

    def test_calculate_basic(self, client):
        """Test basic cost calculation."""
        response = client.post(
            "/pricing/calculate",
            json={
                "input_tokens_monthly": 1000000,
                "output_tokens_monthly": 500000
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "calculated_at" in data
        assert "results" in data
        assert len(data["results"]) > 0
        assert "cheapest" in data
        assert "most_expensive" in data
        assert "savings" in data
        assert "metadata" in data

    def test_calculate_result_structure(self, client):
        """Test that calculation results have correct structure."""
        response = client.post(
            "/pricing/calculate",
            json={
                "input_tokens_monthly": 1000000,
                "output_tokens_monthly": 500000
            }
        )
        data = response.json()
        
        result = data["results"][0]
        assert "provider" in result
        assert "provider_name" in result
        assert "model" in result
        assert "model_name" in result
        assert "monthly_cost" in result
        assert "input_cost" in result
        assert "output_cost" in result
        assert "context_window" in result

    def test_calculate_results_sorted_by_cost(self, client):
        """Test that results are sorted by cost (cheapest first)."""
        response = client.post(
            "/pricing/calculate",
            json={
                "input_tokens_monthly": 1000000,
                "output_tokens_monthly": 500000
            }
        )
        data = response.json()
        
        costs = [r["monthly_cost"] for r in data["results"]]
        assert costs == sorted(costs), "Results should be sorted by cost ascending"

    def test_calculate_with_selected_model(self, client):
        """Test calculation with a selected model."""
        response = client.post(
            "/pricing/calculate",
            json={
                "input_tokens_monthly": 1000000,
                "output_tokens_monthly": 500000,
                "selected_model": "openai/gpt-4o"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Find the selected model in results
        selected = next((r for r in data["results"] if r["is_selected"]), None)
        assert selected is not None, "Selected model should be marked"
        assert selected["provider"] == "openai"
        assert selected["model"] == "gpt-4o"

    def test_calculate_zero_tokens(self, client):
        """Test calculation with zero tokens."""
        response = client.post(
            "/pricing/calculate",
            json={
                "input_tokens_monthly": 0,
                "output_tokens_monthly": 0
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # All costs should be zero
        for result in data["results"]:
            assert result["monthly_cost"] == 0.0

    def test_calculate_negative_tokens_rejected(self, client):
        """Test that negative token values are rejected."""
        response = client.post(
            "/pricing/calculate",
            json={
                "input_tokens_monthly": -1000,
                "output_tokens_monthly": 500000
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_calculate_get_version(self, client):
        """Test GET version of calculate endpoint for shareable URLs."""
        response = client.get(
            "/pricing/calculate",
            params={
                "input_tokens": 1000000,
                "output_tokens": 500000
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert len(data["results"]) > 0

    def test_calculate_get_default_values(self, client):
        """Test GET version uses default values when no params provided."""
        response = client.get("/pricing/calculate")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        # Default is 1M input, 500K output
        assert data["usage"]["input_tokens"] == 1000000
        assert data["usage"]["output_tokens"] == 500000


class TestPricingCompare:
    """Test the model comparison endpoint."""

    def test_compare_two_models(self, client):
        """Test comparing two models."""
        response = client.post(
            "/pricing/compare",
            json={
                "models": ["openai/gpt-4o", "anthropic/claude-sonnet-45"],
                "input_tokens_monthly": 1000000,
                "output_tokens_monthly": 500000
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert len(data["models"]) == 2
        assert "cheapest" in data
        assert "most_expensive" in data
        assert "max_savings" in data

    def test_compare_model_structure(self, client):
        """Test that compared models have correct structure."""
        response = client.post(
            "/pricing/compare",
            json={
                "models": ["openai/gpt-4o", "openai/gpt-4o-mini"],
                "input_tokens_monthly": 1000000,
                "output_tokens_monthly": 500000
            }
        )
        data = response.json()
        
        model = data["models"][0]
        assert "provider" in model
        assert "model" in model
        assert "monthly_cost" in model
        assert "cost_rank" in model
        assert "cost_vs_cheapest" in model
        assert "cost_vs_cheapest_amount" in model

    def test_compare_results_ranked(self, client):
        """Test that compared models are ranked by cost."""
        response = client.post(
            "/pricing/compare",
            json={
                "models": ["openai/gpt-4o", "openai/gpt-4o-mini", "anthropic/claude-sonnet-45"],
                "input_tokens_monthly": 1000000,
                "output_tokens_monthly": 500000
            }
        )
        data = response.json()
        
        # Check ranks are sequential
        ranks = [m["cost_rank"] for m in data["models"]]
        assert ranks == [1, 2, 3]
        
        # Check cheapest has rank 1
        assert data["models"][0]["cost_rank"] == 1
        assert data["models"][0]["cost_vs_cheapest_amount"] == 0.0

    def test_compare_invalid_model_format(self, client):
        """Test that invalid model format is rejected."""
        response = client.post(
            "/pricing/compare",
            json={
                "models": ["invalid-model", "openai/gpt-4o"],
                "input_tokens_monthly": 1000000,
                "output_tokens_monthly": 500000
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid model format" in response.json()["detail"]

    def test_compare_unknown_provider(self, client):
        """Test that unknown provider is rejected."""
        response = client.post(
            "/pricing/compare",
            json={
                "models": ["unknown/model", "openai/gpt-4o"],
                "input_tokens_monthly": 1000000,
                "output_tokens_monthly": 500000
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unknown provider" in response.json()["detail"]

    def test_compare_unknown_model(self, client):
        """Test that unknown model is rejected."""
        response = client.post(
            "/pricing/compare",
            json={
                "models": ["openai/unknown-model", "openai/gpt-4o"],
                "input_tokens_monthly": 1000000,
                "output_tokens_monthly": 500000
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unknown model" in response.json()["detail"]

    def test_compare_single_model_rejected(self, client):
        """Test that comparing single model is rejected."""
        response = client.post(
            "/pricing/compare",
            json={
                "models": ["openai/gpt-4o"],
                "input_tokens_monthly": 1000000,
                "output_tokens_monthly": 500000
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestPricingSubscribe:
    """Test the email subscription endpoint."""

    def test_subscribe_valid_email(self, client):
        """Test subscribing with a valid email."""
        response = client.post(
            "/pricing/alerts/subscribe",
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
            "/pricing/alerts/subscribe",
            json={"email": "not-an-email"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestPricingWidget:
    """Test the widget endpoint."""

    def test_get_widget(self, client):
        """Test getting the widget HTML."""
        response = client.get("/pricing/widget")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        
        html = response.text
        assert "pricing" in html.lower()

    def test_widget_is_self_contained(self, client):
        """Test that widget contains all necessary CSS and JS."""
        response = client.get("/pricing/widget")
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


class TestPricingIntegration:
    """Integration tests for pricing calculator."""

    def test_full_flow(self, client):
        """Test the full flow: get models, calculate, compare, subscribe."""
        # 1. Get all models
        models_response = client.get("/pricing/models")
        assert models_response.status_code == status.HTTP_200_OK
        
        # 2. Calculate costs
        calculate_response = client.post(
            "/pricing/calculate",
            json={
                "input_tokens_monthly": 1000000,
                "output_tokens_monthly": 500000
            }
        )
        assert calculate_response.status_code == status.HTTP_200_OK
        
        # 3. Compare specific models
        compare_response = client.post(
            "/pricing/compare",
            json={
                "models": ["openai/gpt-4o", "openai/gpt-4o-mini"],
                "input_tokens_monthly": 1000000,
                "output_tokens_monthly": 500000
            }
        )
        assert compare_response.status_code == status.HTTP_200_OK
        
        # 4. Subscribe to alerts
        subscribe_response = client.post(
            "/pricing/alerts/subscribe",
            json={"email": "test@example.com"}
        )
        assert subscribe_response.status_code == status.HTTP_200_OK
        
        # 5. Get widget
        widget_response = client.get("/pricing/widget")
        assert widget_response.status_code == status.HTTP_200_OK

    def test_calculation_matches_model_data(self, client):
        """Test that calculation uses correct pricing from model data."""
        # Get model data
        models_response = client.get("/pricing/models")
        models_data = models_response.json()
        
        gpt4o = models_data["providers"]["openai"]["models"]["gpt-4o"]
        input_per_1m = gpt4o["input_per_1m"]
        output_per_1m = gpt4o["output_per_1m"]
        
        # Calculate expected cost
        input_tokens = 1000000
        output_tokens = 500000
        expected_input_cost = (input_tokens / 1000000) * input_per_1m
        expected_output_cost = (output_tokens / 1000000) * output_per_1m
        expected_total = expected_input_cost + expected_output_cost
        
        # Get calculated cost
        calc_response = client.post(
            "/pricing/calculate",
            json={
                "input_tokens_monthly": input_tokens,
                "output_tokens_monthly": output_tokens
            }
        )
        calc_data = calc_response.json()
        
        # Find GPT-4o in results
        gpt4o_result = next(
            (r for r in calc_data["results"] if r["provider"] == "openai" and r["model"] == "gpt-4o"),
            None
        )
        
        assert gpt4o_result is not None
        assert abs(gpt4o_result["monthly_cost"] - expected_total) < 0.01
