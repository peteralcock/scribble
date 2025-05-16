import pytest
import sys
import os
from uuid import uuid4
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Subscription, Order
from datetime import datetime, timedelta

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN', 'supersecrettoken')

@pytest.fixture
def client(tmp_path):
    # Use a unique SQLite file per test function
    db_path = tmp_path / f"test_{uuid4().hex}.db"
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_subscription_list_endpoint(client):
    """Test the subscription list endpoint"""
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = client.get('/v1/coding_test/subscriptions/1?per_page=10', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'subscriptions' in data
    assert 'total_count' in data

def test_order_detail_endpoint(client):
    """Test the order detail endpoint"""
    # Create test data
    with app.app_context():
        subscription = Subscription(
            billing_interval__c="1 month",
            status__c="active",
            start_date__c=datetime.now()
        )
        db.session.add(subscription)
        db.session.commit()
        order = Order(
            closedate=datetime.now(),
            total_order_value__c=99.99,
            parent_subscription_id__c=subscription.id
        )
        db.session.add(order)
        db.session.commit()
        order_id = order.id  # Store before session closes

    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = client.get(f'/v1/coding_test/order/{order_id}', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == order_id
    assert data['total_order_value__c'] == 99.99

def test_subscription_orders_endpoint(client):
    """Test the subscription orders endpoint"""
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = client.get('/v1/coding_test/orders/1/1', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'orders' in data
    assert 'total_count' in data

def test_subscription_statistics(client):
    """Test subscription statistics calculation"""
    with app.app_context():
        # Create test subscriptions
        subscriptions = [
            Subscription(
                billing_interval__c="1 month",
                status__c=status,
                start_date__c=datetime.now() - timedelta(days=30*i)
            ) for i, status in enumerate(['active', 'active', 'on-hold', 'canceled'])
        ]
        db.session.add_all(subscriptions)
        db.session.commit()

    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = client.get('/v1/coding_test/statistics', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_subscriptions'] == 4
    assert data['active_subscriptions'] == 2
    assert data['on_hold_subscriptions'] == 1
    assert data['canceled_subscriptions'] == 1
    assert 'average_subscription_length' in data

def test_create_subscription_model(client):
    """Simulate customer signup by creating a Subscription object directly."""
    with app.app_context():
        subscription = Subscription(
            billing_interval__c="1 month",
            status__c="active",
            start_date__c=datetime.now()
        )
        db.session.add(subscription)
        db.session.commit()
        assert subscription.id is not None
        fetched = db.session.get(Subscription, subscription.id)
        assert fetched is not None
        assert fetched.status__c == "active"

def test_successful_renewal_creates_order(client):
    """Simulate a successful renewal by creating an Order for an existing Subscription."""
    with app.app_context():
        subscription = Subscription(
            billing_interval__c="1 month",
            status__c="active",
            start_date__c=datetime.now()
        )
        db.session.add(subscription)
        db.session.commit()
        order = Order(
            closedate=datetime.now(),
            total_order_value__c=49.99,
            parent_subscription_id__c=subscription.id
        )
        db.session.add(order)
        db.session.commit()
        assert order.id is not None
        fetched_order = db.session.get(Order, order.id)
        assert fetched_order is not None
        assert fetched_order.parent_subscription_id__c == subscription.id 

def test_create_subscription_api(client):
    """Test the POST endpoint for creating a subscription."""
    payload = {
        "billing_interval__c": "1 month",
        "status__c": "active",
        "start_date__c": datetime.now().isoformat(),
        "end_date__c": None,
        "next_payment_date__c": None,
        "recurring_amount__c": 19.99
    }
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = client.post('/v1/coding_test/subscription', json=payload, headers=headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data['billing_interval__c'] == "1 month"
    assert data['status__c'] == "active"
    assert data['recurring_amount__c'] == 19.99
    assert data['id'] is not None

def test_renew_subscription_api_success(client):
    """Test the POST endpoint for renewing a subscription (success case)."""
    # First, create a subscription
    payload = {
        "billing_interval__c": "1 month",
        "status__c": "active",
        "start_date__c": datetime.now().isoformat(),
        "end_date__c": None,
        "next_payment_date__c": None,
        "recurring_amount__c": 19.99
    }
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    create_resp = client.post('/v1/coding_test/subscription', json=payload, headers=headers)
    subscription_id = create_resp.get_json()['id']

    # Now, renew the subscription (success)
    renew_payload = {"success": True, "total_order_value__c": 29.99}
    renew_resp = client.post(f'/v1/coding_test/subscription/{subscription_id}/renew', json=renew_payload, headers=headers)
    assert renew_resp.status_code == 201
    data = renew_resp.get_json()
    assert data['order_created'] is True
    assert data['total_order_value__c'] == 29.99
    assert data['parent_subscription_id__c'] == subscription_id

def test_renew_subscription_api_failure(client):
    """Test the POST endpoint for renewing a subscription (failure case, no order created)."""
    # First, create a subscription
    payload = {
        "billing_interval__c": "1 month",
        "status__c": "active",
        "start_date__c": datetime.now().isoformat(),
        "end_date__c": None,
        "next_payment_date__c": None,
        "recurring_amount__c": 19.99
    }
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    create_resp = client.post('/v1/coding_test/subscription', json=payload, headers=headers)
    subscription_id = create_resp.get_json()['id']

    # Now, renew the subscription (failure)
    renew_payload = {"success": False}
    renew_resp = client.post(f'/v1/coding_test/subscription/{subscription_id}/renew', json=renew_payload, headers=headers)
    assert renew_resp.status_code == 200
    data = renew_resp.get_json()
    assert data['order_created'] is False

def test_subscription_fields_and_types(client):
    """Ensure Subscription fields and types are correct."""
    with app.app_context():
        subscription = Subscription(
            billing_interval__c="1 month",
            status__c="active",
            start_date__c=datetime.now(),
            end_date__c=None,
            next_payment_date__c=None,
            recurring_amount__c=10.0
        )
        db.session.add(subscription)
        db.session.commit()
        # 1. id is int and unique
        assert isinstance(subscription.id, int)
        # 2. billing_interval__c is str
        assert isinstance(subscription.billing_interval__c, str)
        # 3. end_date__c is None or datetime
        assert subscription.end_date__c is None or isinstance(subscription.end_date__c, datetime)
        # 4. next_payment_date__c is None or datetime
        assert subscription.next_payment_date__c is None or isinstance(subscription.next_payment_date__c, datetime)
        # 5. recurring_amount__c is None or float
        assert subscription.recurring_amount__c is None or isinstance(subscription.recurring_amount__c, float)
        # 6. start_date__c is datetime
        assert isinstance(subscription.start_date__c, datetime)
        # 7. status__c is one of allowed values
        assert subscription.status__c in ("active", "canceled", "on-hold")

def test_order_fields_and_types(client):
    """Ensure Order fields and types are correct and parent_subscription_id__c references a valid subscription."""
    with app.app_context():
        subscription = Subscription(
            billing_interval__c="1 month",
            status__c="active",
            start_date__c=datetime.now()
        )
        db.session.add(subscription)
        db.session.commit()
        order = Order(
            closedate=datetime.now(),
            total_order_value__c=25.5,
            parent_subscription_id__c=subscription.id
        )
        db.session.add(order)
        db.session.commit()
        # 1. id is int and unique
        assert isinstance(order.id, int)
        # 2. closedate is datetime
        assert isinstance(order.closedate, datetime)
        # 3. total_order_value__c is float
        assert isinstance(order.total_order_value__c, float)
        # 4. parent_subscription_id__c is int and references a valid subscription
        assert isinstance(order.parent_subscription_id__c, int)
        fetched_sub = db.session.get(Subscription, order.parent_subscription_id__c)
        assert fetched_sub is not None 

def test_missed_payments_analysis(client):
    """Test the missed payments analysis endpoint."""
    # Create test subscriptions with different scenarios
    # 1. Monthly subscription with missed payments
    monthly_sub = Subscription(
        billing_interval__c="1 month",
        status__c="active",
        start_date__c=datetime(2024, 1, 1),
        recurring_amount__c=10.0
    )
    db.session.add(monthly_sub)
    db.session.commit()
    
    # Add only 2 orders for a subscription that should have 3
    for i in range(2):
        order = Order(
            closedate=datetime(2024, i+1, 1),
            total_order_value__c=10.0,
            parent_subscription_id__c=monthly_sub.id
        )
        db.session.add(order)
    
    # 2. On-hold subscription with missed payments
    on_hold_sub = Subscription(
        billing_interval__c="1 month",
        status__c="on-hold",
        start_date__c=datetime(2024, 1, 1),
        recurring_amount__c=20.0
    )
    db.session.add(on_hold_sub)
    db.session.commit()
    
    # Add only 1 order for a subscription that should have 3
    order = Order(
        closedate=datetime(2024, 1, 1),
        total_order_value__c=20.0,
        parent_subscription_id__c=on_hold_sub.id
    )
    db.session.add(order)
    
    db.session.commit()
    
    # Test the endpoint as of March 31, 2024
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = client.get('/v1/coding_test/analysis/missed-payments?as_of=2024-03-31T23:59:59', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    
    # Verify totals
    assert data['total_missed_payments'] == 3  # 1 missed for monthly + 2 missed for on-hold
    assert data['total_missed_value'] == 50.0  # (1 * 10.0) + (2 * 20.0)
    
    # Verify details
    assert len(data['details']) == 2  # Two subscriptions with missed payments
    
    # Verify monthly subscription details
    monthly_details = next(d for d in data['details'] if d['subscription_id'] == monthly_sub.id)
    assert monthly_details['missed_payments'] == 1
    assert monthly_details['missed_value'] == 10.0
    
    # Verify on-hold subscription details
    on_hold_details = next(d for d in data['details'] if d['subscription_id'] == on_hold_sub.id)
    assert on_hold_details['missed_payments'] == 2
    assert on_hold_details['missed_value'] == 40.0 