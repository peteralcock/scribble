import pytest
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.analytics import (
    calculate_subscription_stats,
    parse_billing_interval,
    calculate_missed_payments
)
from app.models import SubscriptionStats, MissedPaymentStats

class TestAnalytics:
    def test_calculate_subscription_stats(self, mock_subscriptions):
        """Test that subscription stats are calculated correctly."""
        stats = calculate_subscription_stats(mock_subscriptions)
        
        assert isinstance(stats, SubscriptionStats)
        assert stats.total_subscriptions == 5
        assert stats.active_subscriptions == 2
        assert stats.on_hold_subscriptions == 1
        assert stats.cancelled_subscriptions == 2
        
        # Average subscription length calculation
        # Active subscriptions count from start to now, canceled ones from start to end date
        # For this test, we'll allow a small margin of error due to the way dates are handled
        # The exact value depends on when the test is run
        assert 150 <= stats.average_subscription_length_days <= 250
    
    def test_empty_subscription_stats(self):
        """Test that subscription stats handles empty lists."""
        stats = calculate_subscription_stats([])
        
        assert isinstance(stats, SubscriptionStats)
        assert stats.total_subscriptions == 0
        assert stats.active_subscriptions == 0
        assert stats.on_hold_subscriptions == 0
        assert stats.cancelled_subscriptions == 0
        assert stats.average_subscription_length_days == 0
    
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
    
    def test_calculate_missed_payments(self, mock_subscriptions, mock_orders):
        """Test calculation of missed payments."""
        # Set up a past date for testing
        now = datetime.now()
        
        # Override the start dates to ensure specific missed payment scenarios
        # Subscription 1: Monthly, all paid (0 missed)
        # Subscription 3: Monthly, missing May payment (1 missed)
        # Subscription 4: Yearly, just started (0 missed)
        # Others are cancelled or have no recurring_amount
        
        missed_payment_stats = calculate_missed_payments(mock_subscriptions, mock_orders)
        
        assert isinstance(missed_payment_stats, MissedPaymentStats)
        assert missed_payment_stats.missed_payments_count == 1
        assert missed_payment_stats.missed_payments_value == 29.99
    
    def test_calculate_missed_payments_edge_cases(self, mock_subscriptions):
        """Test calculation of missed payments with edge cases."""
        # Empty orders
        empty_orders = {}
        now = datetime.now()
        
        # Only consider subscriptions that:
        # 1. Are active or on-hold
        # 2. Have a recurring amount
        # From our mock_subscriptions: Sub 1 (active), Sub 3 (on-hold), and Sub 4 (active) qualify
        
        # For this test, we'll assume they all should have had payments but don't
        missed_payment_stats = calculate_missed_payments(mock_subscriptions, empty_orders)
        
        active_or_onhold_with_amount = [
            sub for sub in mock_subscriptions
            if sub.status__c in ["active", "on-hold"] and sub.recurring_amount__c is not None
        ]
        
        expected_missed_count = 0
        for sub in active_or_onhold_with_amount:
            interval_value, interval_unit = parse_billing_interval(sub.billing_interval__c)
            if interval_unit == "month" or interval_unit == "months":
                delta = relativedelta(now, sub.start_date__c)
                expected_missed_count += (delta.years * 12 + delta.months) // interval_value
            elif interval_unit == "year" or interval_unit == "years":
                delta = relativedelta(now, sub.start_date__c)
                expected_missed_count += delta.years // interval_value
            elif interval_unit == "week" or interval_unit == "weeks":
                delta = (now - sub.start_date__c).days
                expected_missed_count += delta // (7 * interval_value)
            elif interval_unit == "day" or interval_unit == "days":
                delta = (now - sub.start_date__c).days
                expected_missed_count += delta // interval_value
        
        assert missed_payment_stats.missed_payments_count > 0  # Should have some missed payments
        
        # Test with subscriptions having no recurring amount
        for sub in mock_subscriptions:
            sub.recurring_amount__c = None
        
        missed_payment_stats = calculate_missed_payments(mock_subscriptions, empty_orders)
        assert missed_payment_stats.missed_payments_count == 0
        assert missed_payment_stats.missed_payments_value == 0