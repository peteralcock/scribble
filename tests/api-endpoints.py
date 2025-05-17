import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime, timezone
from app.main import app
from app.models import Subscription, Order, SubscriptionStats, MissedPaymentStats, AnalyticsResponse

# Create a test client
client = TestClient(app)

# Define mock data directly in this file since fixtures aren't being found
def get_mock_subscriptions():
    return [
        Subscription(
            id=1,
            billing_interval__c="1 month",
            end_date__c=None,
            next_payment_date__c=datetime(2025, 6, 1, tzinfo=timezone.utc),
            recurring_amount__c=29.99,
            start_date__c=datetime(2024, 1, 1, tzinfo=timezone.utc),
            status__c="active"
        ),
        Subscription(
            id=2,
            billing_interval__c="3 months",
            end_date__c=datetime(2024, 10, 1, tzinfo=timezone.utc),
            next_payment_date__c=None,
            recurring_amount__c=79.99,
            start_date__c=datetime(2024, 1, 1, tzinfo=timezone.utc),
            status__c="canceled"
        ),
        Subscription(
            id=3,
            billing_interval__c="1 month",
            end_date__c=None,
            next_payment_date__c=datetime(2025, 6, 15, tzinfo=timezone.utc),
            recurring_amount__c=29.99,
            start_date__c=datetime(2024, 3, 15, tzinfo=timezone.utc),
            status__c="on-hold"
        ),
        Subscription(
            id=4,
            billing_interval__c="1 year",
            end_date__c=None,
            next_payment_date__c=datetime(2026, 1, 1, tzinfo=timezone.utc),
            recurring_amount__c=299.99,
            start_date__c=datetime(2025, 1, 1, tzinfo=timezone.utc),
            status__c="active"
        ),
        Subscription(
            id=5,
            billing_interval__c="2 weeks",
            end_date__c=datetime(2024, 8, 1, tzinfo=timezone.utc),
            next_payment_date__c=None,
            recurring_amount__c=None,  # Pre-paid
            start_date__c=datetime(2024, 2, 1, tzinfo=timezone.utc),
            status__c="canceled"
        )
    ]

def get_mock_orders():
    return {
        1: [
            Order(
                id=101,
                closedate=datetime(2024, 1, 1, tzinfo=timezone.utc),
                total_order_value__c=29.99,
                parent_subscription_id__c=1
            ),
            Order(
                id=102,
                closedate=datetime(2024, 2, 1, tzinfo=timezone.utc),
                total_order_value__c=29.99,
                parent_subscription_id__c=1
            ),
        ],
        3: [
            Order(
                id=301,
                closedate=datetime(2024, 3, 15, tzinfo=timezone.utc),
                total_order_value__c=29.99,
                parent_subscription_id__c=3
            ),
        ]
    }

class TestAPIEndpoints:
    
    @pytest.mark.asyncio
    async def test_analytics_endpoint_success(self):
        """Test the /analytics endpoint with mocked data."""
        with patch('app.main.get_api_client') as mock_get_api_client:
            # Setup mock API client
            mock_api_client = AsyncMock()
            mock_api_client.get_subscriptions.return_value = get_mock_subscriptions()
            
            # Mock the get_subscription_orders to return data from our mock_orders
            async def mock_get_orders(sub_id):
                return get_mock_orders().get(sub_id, [])
            
            mock_api_client.get_subscription_orders.side_effect = mock_get_orders
            
            # Set up the context manager mock
            context_manager = MagicMock()
            context_manager.__aenter__.return_value = mock_api_client
            mock_get_api_client.return_value = context_manager
            
            # Make the request
            response = client.get("/analytics")
            
            # Assert successful response
            assert response.status_code == 200
            
            # Parse response data
            data = response.json()
            
            # Verify structure
            assert "subscription_stats" in data
            assert "missed_payment_stats" in data
            
            # Verify subscription stats
            sub_stats = data["subscription_stats"]
            assert sub_stats["total_subscriptions"] == 5
            assert sub_stats["active_subscriptions"] == 2
            assert sub_stats["on_hold_subscriptions"] == 1
            assert sub_stats["cancelled_subscriptions"] == 2
            
            # Verify missed payments (exact values depend on the test data and current date)
            missed_payments = data["missed_payment_stats"]
            assert "missed_payments_count" in missed_payments
            assert "missed_payments_value" in missed_payments
            
            # Ensure API client was called correctly
            mock_api_client.get_subscriptions.assert_called_once()
            assert mock_api_client.get_subscription_orders.call_count == 5  # Once for each subscription
    
    @pytest.mark.asyncio
    async def test_analytics_endpoint_no_subscriptions(self):
        """Test the /analytics endpoint when no subscriptions are found."""
        with patch('app.main.get_api_client') as mock_get_api_client:
            # Setup mock to return empty list
            mock_api_client = AsyncMock()
            mock_api_client.get_subscriptions.return_value = []
            
            # Set up the context manager mock
            context_manager = MagicMock()
            context_manager.__aenter__.return_value = mock_api_client
            mock_get_api_client.return_value = context_manager
            
            # Make the request
            response = client.get("/analytics")
            
            # Assert error response (404 Not Found)
            assert response.status_code == 404
            assert "No subscriptions found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_analytics_endpoint_api_error(self):
        """Test the /analytics endpoint when the API client raises an exception."""
        with patch('app.main.get_api_client') as mock_get_api_client:
            # Setup mock to raise an exception
            mock_api_client = AsyncMock()
            mock_api_client.get_subscriptions.side_effect = Exception("API Connection Error")
            
            # Set up the context manager mock
            context_manager = MagicMock()
            context_manager.__aenter__.return_value = mock_api_client
            mock_get_api_client.return_value = context_manager
            
            # Make the request
            response = client.get("/analytics")
            
            # Assert error response (500 Internal Server Error)
            assert response.status_code == 500
            assert "API Connection Error" in response.json()["detail"]
    
    def test_docs_endpoint(self):
        """Test that API documentation endpoints are available."""
        # Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()
        
        # ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()