import pytest
from app import app, db
from models import Subscription, Order
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['API_TOKEN'] = os.getenv('API_TOKEN', 'supersecrettoken')
    
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            yield client

@pytest.fixture
def auth_headers():
    return {'Authorization': f'Bearer {app.config["API_TOKEN"]}'}

@pytest.fixture
def sample_subscription():
    return {
        'billing_interval__c': '1 month',
        'status__c': 'active',
        'start_date__c': datetime.now().isoformat(),
        'recurring_amount__c': 29.99
    }

@pytest.fixture
def sample_order():
    return {
        'closedate': datetime.now().isoformat(),
        'total_order_value__c': 29.99
    }

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/healthz')
    assert response.status_code == 200
    assert response.json['status'] == 'ok'

def test_api_docs(client):
    """Test the API documentation endpoint."""
    response = client.get('/docs')
    assert response.status_code == 200
    assert 'swagger-ui' in response.text

def test_subscription_list(client, auth_headers):
    """Test the subscription list endpoint."""
    # Create test subscriptions
    with app.app_context():
        for i in range(3):
            sub = Subscription(
                billing_interval__c='1 month',
                status__c='active',
                start_date__c=datetime.now()
            )
            db.session.add(sub)
        db.session.commit()

    response = client.get('/v1/coding_test/subscriptions/1', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    assert 'subscriptions' in data
    assert 'total_count' in data
    assert len(data['subscriptions']) > 0

def test_subscription_detail(client, auth_headers):
    """Test the subscription detail endpoint."""
    # Create test subscription
    with app.app_context():
        sub = Subscription(
            billing_interval__c='1 month',
            status__c='active',
            start_date__c=datetime.now()
        )
        db.session.add(sub)
        db.session.commit()
        sub_id = sub.id

    response = client.get(f'/v1/coding_test/subscription/{sub_id}', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    assert data['id'] == sub_id
    assert data['status__c'] == 'active'

def test_create_subscription(client, auth_headers, sample_subscription):
    """Test subscription creation endpoint."""
    response = client.post(
        '/v1/coding_test/subscription',
        json=sample_subscription,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json
    assert data['billing_interval__c'] == sample_subscription['billing_interval__c']
    assert data['status__c'] == sample_subscription['status__c']

def test_renew_subscription(client, auth_headers):
    """Test subscription renewal endpoint."""
    # Create test subscription
    with app.app_context():
        sub = Subscription(
            billing_interval__c='1 month',
            status__c='active',
            start_date__c=datetime.now()
        )
        db.session.add(sub)
        db.session.commit()
        sub_id = sub.id

    # Test successful renewal
    response = client.post(
        f'/v1/coding_test/subscription/{sub_id}/renew',
        json={'success': True, 'total_order_value__c': 29.99},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json
    assert data['order_created'] is True
    assert data['total_order_value__c'] == 29.99

    # Test failed renewal
    response = client.post(
        f'/v1/coding_test/subscription/{sub_id}/renew',
        json={'success': False},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json
    assert data['order_created'] is False

def test_order_detail(client, auth_headers):
    """Test the order detail endpoint."""
    # Create test order
    with app.app_context():
        sub = Subscription(
            billing_interval__c='1 month',
            status__c='active',
            start_date__c=datetime.now()
        )
        db.session.add(sub)
        db.session.commit()
        
        order = Order(
            closedate=datetime.now(),
            total_order_value__c=29.99,
            parent_subscription_id__c=sub.id
        )
        db.session.add(order)
        db.session.commit()
        order_id = order.id

    response = client.get(f'/v1/coding_test/order/{order_id}', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    assert data['id'] == order_id
    assert data['total_order_value__c'] == 29.99

def test_subscription_orders(client, auth_headers):
    """Test the subscription orders endpoint."""
    # Create test subscription with orders
    with app.app_context():
        sub = Subscription(
            billing_interval__c='1 month',
            status__c='active',
            start_date__c=datetime.now()
        )
        db.session.add(sub)
        db.session.commit()
        
        for i in range(3):
            order = Order(
                closedate=datetime.now(),
                total_order_value__c=29.99,
                parent_subscription_id__c=sub.id
            )
            db.session.add(order)
        db.session.commit()
        sub_id = sub.id

    response = client.get(f'/v1/coding_test/orders/{sub_id}/1', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    assert 'orders' in data
    assert 'total_count' in data
    assert len(data['orders']) > 0

def test_statistics(client, auth_headers):
    """Test the statistics endpoint."""
    # Create test subscriptions
    with app.app_context():
        subscriptions = [
            Subscription(
                billing_interval__c='1 month',
                status__c=status,
                start_date__c=datetime.now()
            ) for status in ['active', 'active', 'on-hold', 'canceled']
        ]
        db.session.add_all(subscriptions)
        db.session.commit()

    response = client.get('/v1/coding_test/statistics', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    assert data['total_subscriptions'] == 4
    assert data['active_subscriptions'] == 2
    assert data['on_hold_subscriptions'] == 1
    assert data['canceled_subscriptions'] == 1

def test_missed_payments_analysis(client, auth_headers):
    """Test the missed payments analysis endpoint."""
    # Create test subscription with missed payments
    with app.app_context():
        sub = Subscription(
            billing_interval__c='1 month',
            status__c='active',
            start_date__c=datetime.now() - timedelta(days=90),
            recurring_amount__c=29.99
        )
        db.session.add(sub)
        db.session.commit()
        
        # Add only one order for a subscription that should have three
        order = Order(
            closedate=datetime.now() - timedelta(days=30),
            total_order_value__c=29.99,
            parent_subscription_id__c=sub.id
        )
        db.session.add(order)
        db.session.commit()

    response = client.get('/v1/coding_test/analysis/missed-payments', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    assert 'total_missed_payments' in data
    assert 'total_missed_value' in data
    assert 'details' in data
    assert len(data['details']) > 0

def test_authentication(client):
    """Test authentication requirements."""
    # Test without authentication
    response = client.get('/v1/coding_test/subscriptions/1')
    assert response.status_code == 401

    # Test with invalid token
    response = client.get('/v1/coding_test/subscriptions/1', 
                         headers={'Authorization': 'Bearer invalid_token'})
    assert response.status_code == 401

def test_rate_limiting(client, auth_headers):
    """Test rate limiting."""
    # Make multiple requests in quick succession
    for _ in range(5):
        response = client.get('/v1/coding_test/statistics', headers=auth_headers)
        assert response.status_code == 200

def test_invalid_inputs(client, auth_headers):
    """Test handling of invalid inputs."""
    # Test invalid subscription creation
    response = client.post(
        '/v1/coding_test/subscription',
        json={'invalid': 'data'},
        headers=auth_headers
    )
    assert response.status_code == 400

    # Test invalid renewal
    response = client.post(
        '/v1/coding_test/subscription/999/renew',
        json={'invalid': 'data'},
        headers=auth_headers
    )
    assert response.status_code in (400, 404)

def test_not_found_handling(client, auth_headers):
    """Test handling of non-existent resources."""
    # Test non-existent subscription
    response = client.get('/v1/coding_test/subscription/999', headers=auth_headers)
    assert response.status_code == 404

    # Test non-existent order
    response = client.get('/v1/coding_test/order/999', headers=auth_headers)
    assert response.status_code == 404 