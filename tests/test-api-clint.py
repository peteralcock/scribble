import pytest
import pytest_asyncio
import httpx
from app.api_client import AudicusAPIClient

@pytest_asyncio.fixture
async def api_client():
    """Fixture for the API client."""
    client = AudicusAPIClient()
    yield client
    await client.close()

class TestAudicusAPIClient:
    
    @pytest.mark.asyncio
    async def test_get_subscriptions(self, api_client, mock_api_responses):
        """Test fetching subscriptions with successful response."""
        subscriptions = await api_client.get_subscriptions()
        
        # Should have fetched all 5 subscriptions from the mock
        assert len(subscriptions) == 5
        
        # Verify subscription data
        sub_ids = [sub.id for sub in subscriptions]
        assert set(sub_ids) == {1, 2, 3, 4, 5}
        
        # Check specific subscription details
        for sub in subscriptions:
            if sub.id == 1:
                assert sub.status__c == "active"
                assert sub.billing_interval__c == "1 month"
                assert sub.recurring_amount__c == 29.99
            elif sub.id == 3:
                assert sub.status__c == "on-hold"
    
    @pytest.mark.asyncio
    async def test_get_subscription_orders(self, api_client, mock_api_responses):
        """Test fetching orders for a subscription with successful response."""
        # Subscription 1 has orders across multiple pages
        orders = await api_client.get_subscription_orders(1)
        
        # Should have fetched all 5 orders from the mock
        assert len(orders) == 5
        
        # Verify order IDs
        order_ids = [order.id for order in orders]
        assert set(order_ids) == {101, 102, 103, 104, 105}
        
        # Check specific order details
        for order in orders:
            assert order.parent_subscription_id__c == 1
            assert order.total_order_value__c == 29.99
    
    @pytest.mark.asyncio
    async def test_empty_subscription_response(self, api_client, mock_api_responses):
        """Test handling empty subscription response."""
        # Mock returns empty list for page 3
        subscriptions = await api_client.get_subscriptions(per_page=2)  # Force pagination
        
        # Should still get all 5 subscriptions
        assert len(subscriptions) == 5
    
    @pytest.mark.asyncio
    async def test_error_response(self, api_client, mock_api_responses):
        """Test error handling in API client."""
        # Mock returns 404 for subscription 999
        orders = await api_client.get_subscription_orders(999)
        
        # Should return an empty list on error
        assert orders == []
    
    @pytest.mark.asyncio
    async def test_date_parsing(self, api_client, mock_api_responses):
        """Test that dates are parsed correctly from API responses."""
        subscriptions = await api_client.get_subscriptions()
        
        for sub in subscriptions:
            if sub.start_date__c:
                assert isinstance(sub.start_date__c, datetime)
            
            if sub.end_date__c:
                assert isinstance(sub.end_date__c, datetime)
            
            if sub.next_payment_date__c:
                assert isinstance(sub.next_payment_date__c, datetime)
        
        orders = await api_client.get_subscription_orders(1)
        for order in orders:
            assert isinstance(order.closedate, datetime)