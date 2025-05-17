import pytest
from app.models import Subscription, Order, SubscriptionStats, MissedPaymentStats
from datetime import datetime, timezone

class TestModelsSimple:
    
    def test_subscription_model_valid(self):
        """Test that the Subscription model validates with valid data."""
        # Create valid subscription
        subscription = Subscription(
            id=1,
            billing_interval__c="1 month",
            start_date__c=datetime(2024, 1, 1, tzinfo=timezone.utc),
            status__c="active",
            end_date__c=None, 
            next_payment_date__c=None,
            recurring_amount__c=29.99
        )
        
        assert subscription.id == 1
        assert subscription.billing_interval__c == "1 month"
        assert subscription.status__c == "active"
    
    def test_order_model_valid(self):
        """Test that the Order model validates with valid data."""
        order = Order(
            id=101,
            closedate=datetime(2024, 1, 1, tzinfo=timezone.utc),
            total_order_value__c=29.99,
            parent_subscription_id__c=1
        )
        
        assert order.id == 101
        assert order.parent_subscription_id__c == 1
        assert order.total_order_value__c == 29.99
    
    def test_stats_models(self):
        """Test stats models."""
        sub_stats = SubscriptionStats(
            total_subscriptions=10,
            active_subscriptions=5,
            on_hold_subscriptions=2,
            cancelled_subscriptions=3,
            average_subscription_length_days=120.5
        )
        
        assert sub_stats.total_subscriptions == 10
        assert sub_stats.average_subscription_length_days == 120.5
        
        missed_stats = MissedPaymentStats(
            missed_payments_count=3,
            missed_payments_value=89.97
        )
        
        assert missed_stats.missed_payments_count == 3
        assert missed_stats.missed_payments_value == 89.97