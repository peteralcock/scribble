import pytest
from datetime import datetime, timezone
from app.analytics import parse_billing_interval

class TestBillingInterval:
    
    def test_parse_billing_interval(self):
        """Test that billing intervals are parsed correctly."""
        # Test valid formats
        assert parse_billing_interval("1 month") == (1, "month")
        assert parse_billing_interval("3 months") == (3, "months")
        assert parse_billing_interval("1 year") == (1, "year")
        assert parse_billing_interval("2 years") == (2, "years")
        assert parse_billing_interval("14 days") == (14, "day")
        assert parse_billing_interval("2 weeks") == (2, "week")
        
        # Test invalid formats (should default to 1 month)
        assert parse_billing_interval("invalid") == (1, "month")
        assert parse_billing_interval("") == (1, "month")
        assert parse_billing_interval("monthly") == (1, "month")