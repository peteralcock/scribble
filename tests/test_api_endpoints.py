import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import json
from app.main import app
from app.models import Subscription, Order, SubscriptionStats, MissedPaymentStats, AnalyticsResponse

# Create a test client
client = TestClient(app)

class TestAPIEndpoints:
    
    @pytest.mark.asyncio
    @patch('app.main.get_api_client')
    async def test_analytics_endpoint_success(self, mock_get_api_client, mock_subscriptions, mock_orders):
        """Test the /analytics endpoint with mocked data."""
        # Setup mock API client
        mock_api_client = AsyncMock()
        mock_api_client.get_subscriptions.return_value = mock_subscriptions
        
        # Mock the get_subscription_orders to return data from our mock_orders fixture
        async def mock_get_orders(sub_id):
            return mock_orders.get(sub_id, [])
        
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
    @patch('app.main.get_api_client')
    async def test_analytics_endpoint_no_subscriptions(self, mock_get_api_client):
        """Test the /analytics endpoint when no subscriptions are found."""
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
    @patch('app.main.get_api_client')
    async def test_analytics_endpoint_api_error(self, mock_get_api_client):
        """Test the /analytics endpoint when the API client raises an exception."""
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
