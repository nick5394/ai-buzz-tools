"""
Tests for shared utility functions.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestLoadJsonData:
    """Test the JSON data loading function."""

    def test_load_valid_json(self):
        """Test loading a valid JSON file."""
        from api.shared import load_json_data, _data_cache
        
        # Clear cache to ensure fresh load
        _data_cache.clear()
        
        data = load_json_data("pricing_data.json")
        
        assert data is not None
        assert "_metadata" in data
        assert "providers" in data

    def test_load_json_caching(self):
        """Test that JSON data is cached."""
        from api.shared import load_json_data, _data_cache
        
        # Clear cache
        _data_cache.clear()
        
        # First load
        data1 = load_json_data("pricing_data.json")
        
        # Second load should return cached data
        data2 = load_json_data("pricing_data.json")
        
        assert data1 is data2  # Same object (cached)

    def test_load_different_files(self):
        """Test loading different JSON files."""
        from api.shared import load_json_data, _data_cache
        
        _data_cache.clear()
        
        pricing = load_json_data("pricing_data.json")
        status = load_json_data("status_providers.json")
        errors = load_json_data("error_patterns.json")
        
        assert pricing is not None
        assert status is not None
        assert errors is not None
        
        # Each should be different
        assert pricing is not status
        assert status is not errors

    def test_load_nonexistent_file(self):
        """Test that loading nonexistent file raises error."""
        from api.shared import load_json_data, _data_cache
        
        _data_cache.clear()
        
        with pytest.raises(FileNotFoundError):
            load_json_data("nonexistent_file.json")


class TestSubscribeEmail:
    """Test the email subscription function."""

    def test_subscribe_returns_success_without_mailchimp(self):
        """Test that subscription returns success even without Mailchimp configured."""
        from api.shared import subscribe_email
        
        with patch.dict('os.environ', {}, clear=True):
            result = subscribe_email(
                email="test@example.com",
                tool_name="test-tool",
                interest_tags=["interest:test"],
                success_message="Test success!"
            )
        
        assert result["success"] is True
        assert result["message"] == "Test success!"
        assert result["mailchimp_synced"] is False

    def test_subscribe_with_custom_message(self):
        """Test that custom success message is used."""
        from api.shared import subscribe_email
        
        with patch.dict('os.environ', {}, clear=True):
            result = subscribe_email(
                email="test@example.com",
                tool_name="pricing-calculator",
                interest_tags=["interest:price-alerts"],
                success_message="Custom message here!"
            )
        
        assert result["message"] == "Custom message here!"

    @patch('api.shared.os.getenv')
    @patch('mailchimp_marketing.Client')
    def test_subscribe_with_mailchimp_configured(self, mock_client_class, mock_getenv):
        """Test subscription with Mailchimp configured (mocked)."""
        from api.shared import subscribe_email
        
        # Mock environment variables
        def getenv_side_effect(key, default=None):
            env_vars = {
                'MAILCHIMP_API_KEY': 'test-api-key',
                'MAILCHIMP_LIST_ID': 'test-list-id',
                'MAILCHIMP_SERVER_PREFIX': 'us1'
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        # Mock the Mailchimp client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.lists.set_list_member.return_value = {}
        
        result = subscribe_email(
            email="test@example.com",
            tool_name="test-tool",
            interest_tags=["interest:test"],
            success_message="Success!"
        )
        
        assert result["success"] is True
        assert result["mailchimp_synced"] is True
        
        # Verify Mailchimp was called
        mock_client.lists.set_list_member.assert_called_once()

    @patch('api.shared.os.getenv')
    @patch('mailchimp_marketing.Client')
    def test_subscribe_handles_mailchimp_error(self, mock_client_class, mock_getenv):
        """Test that Mailchimp errors are handled gracefully."""
        from api.shared import subscribe_email
        
        def getenv_side_effect(key, default=None):
            env_vars = {
                'MAILCHIMP_API_KEY': 'test-api-key',
                'MAILCHIMP_LIST_ID': 'test-list-id',
                'MAILCHIMP_SERVER_PREFIX': 'us1'
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        # Mock the Mailchimp client to raise an error
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.lists.set_list_member.side_effect = Exception("API Error")
        
        result = subscribe_email(
            email="test@example.com",
            tool_name="test-tool",
            interest_tags=["interest:test"],
            success_message="Success!"
        )
        
        # Should still return success (graceful degradation)
        assert result["success"] is True
        assert result["mailchimp_synced"] is False


class TestFormatCurrency:
    """Test the currency formatting function."""

    def test_format_large_amount(self):
        """Test formatting amounts over 1000."""
        from api.shared import format_currency
        
        assert format_currency(1234.56) == "$1,234.56"
        assert format_currency(10000) == "$10,000.00"
        assert format_currency(1000000.99) == "$1,000,000.99"

    def test_format_medium_amount(self):
        """Test formatting amounts between 0.01 and 1000."""
        from api.shared import format_currency
        
        assert format_currency(0.01) == "$0.01"
        assert format_currency(1.00) == "$1.00"
        assert format_currency(99.99) == "$99.99"
        assert format_currency(999.99) == "$999.99"

    def test_format_small_amount(self):
        """Test formatting amounts less than 0.01."""
        from api.shared import format_currency
        
        assert format_currency(0.001) == "$0.0010"
        assert format_currency(0.0001) == "$0.0001"
        assert format_currency(0.00123) == "$0.0012"

    def test_format_zero(self):
        """Test formatting zero."""
        from api.shared import format_currency
        
        assert format_currency(0) == "$0.0000"

    def test_format_boundary_values(self):
        """Test boundary values."""
        from api.shared import format_currency
        
        # Just under 1000
        assert format_currency(999.99) == "$999.99"
        # Exactly 1000
        assert format_currency(1000) == "$1,000.00"
        # Just under 0.01
        assert format_currency(0.009) == "$0.0090"


class TestFormatDate:
    """Test the date formatting function."""

    def test_format_iso_date(self):
        """Test formatting ISO date strings."""
        from api.shared import format_date
        
        assert format_date("2026-01-28") == "Jan 28, 2026"
        assert format_date("2025-12-25") == "Dec 25, 2025"
        assert format_date("2026-06-15") == "Jun 15, 2026"

    def test_format_iso_datetime(self):
        """Test formatting ISO datetime strings."""
        from api.shared import format_date
        
        assert format_date("2026-01-28T12:00:00Z") == "Jan 28, 2026"
        assert format_date("2026-01-28T00:00:00+00:00") == "Jan 28, 2026"

    def test_format_unknown(self):
        """Test that 'unknown' returns 'Unknown'."""
        from api.shared import format_date
        
        assert format_date("unknown") == "Unknown"

    def test_format_empty_string(self):
        """Test that empty string returns 'Unknown'."""
        from api.shared import format_date
        
        assert format_date("") == "Unknown"

    def test_format_none(self):
        """Test that None returns 'Unknown'."""
        from api.shared import format_date
        
        assert format_date(None) == "Unknown"

    def test_format_invalid_date(self):
        """Test that invalid date returns original string."""
        from api.shared import format_date
        
        assert format_date("not-a-date") == "not-a-date"
        assert format_date("2026/01/28") == "2026/01/28"

    def test_format_partial_date(self):
        """Test partial date strings."""
        from api.shared import format_date
        
        # Only year-month should return original
        assert format_date("2026-01") == "2026-01"


class TestLoadWidget:
    """Test the widget loading function."""

    def test_load_valid_widget(self):
        """Test loading a valid widget file."""
        from api.shared import load_widget
        
        html = load_widget("error_decoder_widget.html")
        
        assert html is not None
        assert "<style>" in html
        assert "<script>" in html

    def test_load_all_widgets(self):
        """Test that all widget files can be loaded."""
        from api.shared import load_widget
        
        widgets = [
            "error_decoder_widget.html",
            "pricing_calculator_widget.html",
            "status_page_widget.html"
        ]
        
        for widget in widgets:
            html = load_widget(widget)
            assert html is not None
            assert len(html) > 0

    def test_load_nonexistent_widget(self):
        """Test that loading nonexistent widget raises error."""
        from api.shared import load_widget
        
        with pytest.raises(FileNotFoundError):
            load_widget("nonexistent_widget.html")


class TestSharedIntegration:
    """Integration tests for shared utilities."""

    def test_all_data_files_loadable(self):
        """Test that all expected data files can be loaded."""
        from api.shared import load_json_data, _data_cache
        
        _data_cache.clear()
        
        # All data files should be loadable
        pricing = load_json_data("pricing_data.json")
        status = load_json_data("status_providers.json")
        errors = load_json_data("error_patterns.json")
        
        # Each should have _metadata
        assert "_metadata" in pricing
        assert "_metadata" in status
        assert "_metadata" in errors

    def test_format_functions_handle_edge_cases(self):
        """Test format functions with edge cases."""
        from api.shared import format_currency, format_date
        
        # Currency edge cases
        assert "$" in format_currency(0)
        assert "$" in format_currency(0.00001)
        assert "$" in format_currency(999999999.99)
        
        # Date edge cases
        result = format_date("")
        assert result == "Unknown"
