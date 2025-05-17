import pytest
import json
import httpx
from datetime import datetime, timezone
from app.models import Subscription, Order

class TestModels:
    def test_subscription_model(self):
        """Test that the Subscription model validates correctly."""
        # Valid subscription
        valid_data = {
            "id": 1,
            "billing_interval__c": "1 month",
            "end_date__c": None,
            "next_payment_date__c": "2025-06-01T00:00:00Z",
            "recurring_amount__c": 29.99,
            "start_date__c": "2024-01-01T00:00:00Z",
            "status__c": "active"
        }
        
        # Create from dict
        subscription = Subscription(**valid_data)
        assert subscription.id == 1
        assert subscription.billing_interval__c == "1 month"
        assert subscription.end_date__c is None
        assert subscription.next_payment_date__c == datetime(2025, 6, 1, tzinfo=timezone.utc)
        assert subscription.recurring_amount__c == 29.99
        assert subscription.start_date__c == datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert subscription.status__c == "active"
        
        # Convert to dict and back
        subscription_dict = subscription.dict()
        subscription_json = json.dumps(subscription_dict, default=str)
        assert "1 month" in subscription_json
        assert "active" in subscription_json
        
        # Test with missing required fields
        with pytest.raises(ValueError):
            Subscription(
                billing_interval__c="1 month",
                start_date__c="2024-01-01T00:00:00Z",
                status__c="active"
                # Missing id
            )
    
    def test_order_model(self):
        """Test that the Order model validates correctly."""
        # Valid order
        valid_data = {
            "id": 101,
            "closedate": "2024-01-01T00:00:00Z",
            "total_order_value__c": 29.99,
            "parent_subscription_id__c": 1
        }
        
        # Create from dict
        order = Order(**valid_data)
        assert order.id == 101
        assert order.closedate == datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert order.total_order_value__c == 29.99
        assert order.parent_subscription_id__c == 1
        
        # Convert to dict and back
        order_dict = order.dict()
        order_json = json.dumps(order_dict, default=str)
        assert "101" in order_json
        assert "29.99" in order_json
        assert "1" in order_json  # parent_subscription_id__c
        
        # Test with missing required fields
        with pytest.raises(ValueError):
            Order(
                id=101,
                closedate="2024-01-01T00:00:00Z",
                # Missing total_order_value__c
                parent_subscription_id__c=1
            )