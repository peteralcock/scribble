import pytest
import respx
from datetime import datetime, timezone
from typing import List, Dict
from app.models import Subscription, Order

@pytest.fixture
def mock_subscriptions() -> List[Subscription]:
    """
    Fixture providing sample subscription data for testing.
    """
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

@pytest.fixture
def mock_orders() -> Dict[int, List[Order]]:
    """
    Fixture providing sample order data for testing.
    """
    return {
        1: [  # Subscription 1 has monthly payments, all paid
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
            Order(
                id=103,
                closedate=datetime(2024, 3, 1, tzinfo=timezone.utc),
                total_order_value__c=29.99,
                parent_subscription_id__c=1
            ),
            Order(
                id=104,
                closedate=datetime(2024, 4, 1, tzinfo=timezone.utc),
                total_order_value__c=29.99,
                parent_subscription_id__c=1
            ),
            Order(
                id=105,
                closedate=datetime(2024, 5, 1, tzinfo=timezone.utc),
                total_order_value__c=29.99,
                parent_subscription_id__c=1
            )
        ],
        2: [  # Subscription 2 has quarterly payments, all paid
            Order(
                id=201,
                closedate=datetime(2024, 1, 1, tzinfo=timezone.utc),
                total_order_value__c=79.99,
                parent_subscription_id__c=2
            ),
            Order(
                id=202,
                closedate=datetime(2024, 4, 1, tzinfo=timezone.utc),
                total_order_value__c=79.99,
                parent_subscription_id__c=2
            ),
            Order(
                id=203,
                closedate=datetime(2024, 7, 1, tzinfo=timezone.utc),
                total_order_value__c=79.99,
                parent_subscription_id__c=2
            ),
        ],
        3: [  # Subscription 3 has monthly payments, missing one
            Order(
                id=301,
                closedate=datetime(2024, 3, 15, tzinfo=timezone.utc),
                total_order_value__c=29.99,
                parent_subscription_id__c=3
            ),
            Order(
                id=302,
                closedate=datetime(2024, 4, 15, tzinfo=timezone.utc),
                total_order_value__c=29.99,
                parent_subscription_id__c=3
            ),
            # Missing May payment
        ],
        4: [  # Subscription 4 has yearly payments, just started
            Order(
                id=401,
                closedate=datetime(2025, 1, 1, tzinfo=timezone.utc),
                total_order_value__c=299.99,
                parent_subscription_id__c=4
            ),
        ],
        5: []  # Subscription 5 is prepaid, no orders
    }

@pytest.fixture
def mock_api_responses():
    """
    Fixture for mocking API responses using respx.
    """
    with respx.mock(
        base_url="https://jungle.audicus.com/v1/coding_test"
    ) as respx_mock:
        # Mock subscriptions endpoint - page 1
        subscription_response_1 = {
            "subscriptions": [
                {
                    "id": 1,
                    "billing_interval__c": "1 month",
                    "end_date__c": None,
                    "next_payment_date__c": "2025-06-01T00:00:00Z",
                    "recurring_amount__c": 29.99,
                    "start_date__c": "2024-01-01T00:00:00Z",
                    "status__c": "active"
                },
                {
                    "id": 2,
                    "billing_interval__c": "3 months",
                    "end_date__c": "2024-10-01T00:00:00Z",
                    "next_payment_date__c": None,
                    "recurring_amount__c": 79.99,
                    "start_date__c": "2024-01-01T00:00:00Z",
                    "status__c": "canceled"
                },
                {
                    "id": 3,
                    "billing_interval__c": "1 month",
                    "end_date__c": None,
                    "next_payment_date__c": "2025-06-15T00:00:00Z",
                    "recurring_amount__c": 29.99,
                    "start_date__c": "2024-03-15T00:00:00Z",
                    "status__c": "on-hold"
                }
            ]
        }
        
        # Mock subscriptions endpoint - page 2
        subscription_response_2 = {
            "subscriptions": [
                {
                    "id": 4,
                    "billing_interval__c": "1 year",
                    "end_date__c": None,
                    "next_payment_date__c": "2026-01-01T00:00:00Z",
                    "recurring_amount__c": 299.99,
                    "start_date__c": "2025-01-01T00:00:00Z",
                    "status__c": "active"
                },
                {
                    "id": 5,
                    "billing_interval__c": "2 weeks",
                    "end_date__c": "2024-08-01T00:00:00Z",
                    "next_payment_date__c": None,
                    "recurring_amount__c": None,
                    "start_date__c": "2024-02-01T00:00:00Z",
                    "status__c": "canceled"
                }
            ]
        }
        
        # Mock subscriptions endpoint - page 3 (empty)
        subscription_response_3 = {
            "subscriptions": []
        }
        
        # Mock orders endpoint for subscription 1 - page 1
        orders_response_sub1_p1 = {
            "orders": [
                {
                    "id": 101,
                    "closedate": "2024-01-01T00:00:00Z",
                    "total_order_value__c": 29.99,
                    "parent_subscription_id__c": 1
                },
                {
                    "id": 102,
                    "closedate": "2024-02-01T00:00:00Z",
                    "total_order_value__c": 29.99,
                    "parent_subscription_id__c": 1
                },
                {
                    "id": 103,
                    "closedate": "2024-03-01T00:00:00Z",
                    "total_order_value__c": 29.99,
                    "parent_subscription_id__c": 1
                }
            ]
        }
        
        # Mock orders endpoint for subscription 1 - page 2
        orders_response_sub1_p2 = {
            "orders": [
                {
                    "id": 104,
                    "closedate": "2024-04-01T00:00:00Z",
                    "total_order_value__c": 29.99,
                    "parent_subscription_id__c": 1
                },
                {
                    "id": 105,
                    "closedate": "2024-05-01T00:00:00Z",
                    "total_order_value__c": 29.99,
                    "parent_subscription_id__c": 1
                }
            ]
        }
        
        # Mock orders endpoint for subscription 1 - page 3 (empty)
        orders_response_sub1_p3 = {
            "orders": []
        }
        
        # Set up mock routes
        respx_mock.get("/subscriptions/1?per_page=100").respond(
            status_code=200, json=subscription_response_1
        )
        respx_mock.get("/subscriptions/2?per_page=100").respond(
            status_code=200, json=subscription_response_2
        )
        respx_mock.get("/subscriptions/3?per_page=100").respond(
            status_code=200, json=subscription_response_3
        )
        
        respx_mock.get("/orders/1/1").respond(
            status_code=200, json=orders_response_sub1_p1
        )
        respx_mock.get("/orders/1/2").respond(
            status_code=200, json=orders_response_sub1_p2
        )
        respx_mock.get("/orders/1/3").respond(
            status_code=200, json=orders_response_sub1_p3
        )
        
        # Mock the other subscriptions' order endpoints
        for sub_id in [2, 3, 4, 5]:
            respx_mock.get(f"/orders/{sub_id}/1").respond(
                status_code=200, 
                json={"orders": [order.__dict__ for order in mock_orders().get(sub_id, [])]}
            )
            respx_mock.get(f"/orders/{sub_id}/2").respond(
                status_code=200, json={"orders": []}
            )
            
        # Mock error routes
        respx_mock.get("/subscriptions/999?per_page=100").respond(status_code=404)
        respx_mock.get("/orders/999/1").respond(status_code=404)
        
        yield respx_mock
