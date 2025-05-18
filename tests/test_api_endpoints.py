import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app, get_api_client
import asyncio

client = TestClient(app)

class TestAPIEndpoints:
    
    @pytest.mark.asyncio
    async def test_analytics_endpoint_success(self, mock_subscriptions, mock_orders):
        """Test the /analytics endpoint with mocked data from fixtures."""
        mock_api_client_instance = AsyncMock()
        mock_api_client_instance.get_subscriptions.return_value = mock_subscriptions
        
        async def mock_get_orders_side_effect(sub_id: int):
            return mock_orders.get(sub_id, [])
        
        mock_api_client_instance.get_subscription_orders.side_effect = mock_get_orders_side_effect
        
        # Define the dependency override function
        async def override_get_api_client():
            try:
                yield mock_api_client_instance
            finally:
                # Clean up if needed
                if hasattr(mock_api_client_instance, 'aclose') and asyncio.iscoroutinefunction(mock_api_client_instance.aclose):
                    await mock_api_client_instance.aclose()
                elif hasattr(mock_api_client_instance, 'close') and asyncio.iscoroutinefunction(mock_api_client_instance.close):
                    await mock_api_client_instance.close()
                
        # Apply the dependency override
        app.dependency_overrides[get_api_client] = override_get_api_client
        
        try:
            response = client.get("/analytics")
            
            assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
            
            data = response.json()
            
            assert "subscription_stats" in data
            assert "missed_payment_stats" in data
            
            sub_stats_data = data["subscription_stats"]
            assert sub_stats_data["total_subscriptions"] == len(mock_subscriptions)
            
            expected_active = sum(1 for sub in mock_subscriptions if sub.status__c == "active")
            expected_on_hold = sum(1 for sub in mock_subscriptions if sub.status__c == "on-hold")
            expected_cancelled = sum(1 for sub in mock_subscriptions if sub.status__c == "canceled")

            assert sub_stats_data["active_subscriptions"] == expected_active
            assert sub_stats_data["on_hold_subscriptions"] == expected_on_hold
            assert sub_stats_data["cancelled_subscriptions"] == expected_cancelled
            
            missed_payments = data["missed_payment_stats"]
            assert "missed_payments_count" in missed_payments
            assert "missed_payments_value" in missed_payments
            
            mock_api_client_instance.get_subscriptions.assert_called_once()
            assert mock_api_client_instance.get_subscription_orders.call_count == len(mock_subscriptions)
        finally:
            # Clean up the override after the test
            app.dependency_overrides = {}
    
    @pytest.mark.asyncio
    async def test_analytics_endpoint_no_subscriptions(self):
        """Test the /analytics endpoint when no subscriptions are found."""
        mock_api_client_instance = AsyncMock()
        mock_api_client_instance.get_subscriptions.return_value = []
        
        # Define the dependency override function
        async def override_get_api_client():
            try:
                yield mock_api_client_instance
            finally:
                if hasattr(mock_api_client_instance, 'aclose') and asyncio.iscoroutinefunction(mock_api_client_instance.aclose):
                    await mock_api_client_instance.aclose()
                elif hasattr(mock_api_client_instance, 'close') and asyncio.iscoroutinefunction(mock_api_client_instance.close):
                    await mock_api_client_instance.close()
                
        # Apply the dependency override
        app.dependency_overrides[get_api_client] = override_get_api_client
        
        try:
            response = client.get("/analytics")
            
            assert response.status_code == 404, f"Expected 404, got {response.status_code}. Response: {response.text}"
            assert "No subscriptions found" in response.json()["detail"]
        finally:
            # Clean up the override after the test
            app.dependency_overrides = {}
    
    @pytest.mark.asyncio
    async def test_analytics_endpoint_api_error(self):
        """Test the /analytics endpoint when the API client raises an exception."""
        mock_api_client_instance = AsyncMock()
        mock_api_client_instance.get_subscriptions.side_effect = Exception("API Connection Error")
        
        # Define the dependency override function
        async def override_get_api_client():
            try:
                yield mock_api_client_instance
            finally:
                if hasattr(mock_api_client_instance, 'aclose') and asyncio.iscoroutinefunction(mock_api_client_instance.aclose):
                    await mock_api_client_instance.aclose()
                elif hasattr(mock_api_client_instance, 'close') and asyncio.iscoroutinefunction(mock_api_client_instance.close):
                    await mock_api_client_instance.close()
                
        # Apply the dependency override
        app.dependency_overrides[get_api_client] = override_get_api_client
        
        try:
            response = client.get("/analytics")
            
            assert response.status_code == 500, f"Expected 500, got {response.status_code}. Response: {response.text}"
            assert "API Connection Error" in response.json()["detail"]
        finally:
            # Clean up the override after the test
            app.dependency_overrides = {}
    
    def test_docs_endpoint(self):
        """Test that API documentation endpoints are available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()
        
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()

