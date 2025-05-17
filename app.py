import os
from flask import Flask, jsonify, render_template, request, abort
from models import db, Subscription, Order
from datetime import datetime, timedelta
from sqlalchemy import func, text
from dateutil.relativedelta import relativedelta
from flask_restx import Api, Resource, fields
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

app = Flask(__name__)

# Configure SQLAlchemy
if os.getenv('FLASK_ENV') == 'testing':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/clearhear')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

api = Api(app, doc='/docs', title='ClearHear API', description='API for managing subscriptions and orders.')

subscription_model = api.model('Subscription', {
    'id': fields.Integer(readOnly=True),
    'billing_interval__c': fields.String(required=True),
    'end_date__c': fields.String,
    'next_payment_date__c': fields.String,
    'recurring_amount__c': fields.Float,
    'start_date__c': fields.String(required=True),
    'status__c': fields.String(enum=['active', 'canceled', 'on-hold'])
})

order_model = api.model('Order', {
    'id': fields.Integer(readOnly=True),
    'closedate': fields.String,
    'total_order_value__c': fields.Float,
    'parent_subscription_id__c': fields.Integer
})

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN', 'supersecrettoken')

# Configure rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=["100 per hour"]
)

EXEMPT_PATHS = ['/healthz', '/docs', '/swagger.json']

@app.before_request
def require_auth():
    if request.path.startswith(tuple(EXEMPT_PATHS)) or request.path.startswith('/static'):
        return
    token = request.headers.get('Authorization')
    if not token or token != f"Bearer {API_TOKEN}":
        return jsonify({'error': 'Unauthorized'}), 401

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/v1/coding_test/subscriptions/<int:page_number>')
def get_subscriptions(page_number):
    per_page = request.args.get('per_page', default=10, type=int)
    
    subscriptions = Subscription.query.paginate(
        page=page_number,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'subscriptions': [{
            'id': sub.id,
            'billing_interval__c': sub.billing_interval__c,
            'end_date__c': sub.end_date__c.isoformat() if sub.end_date__c else None,
            'next_payment_date__c': sub.next_payment_date__c.isoformat() if sub.next_payment_date__c else None,
            'recurring_amount__c': sub.recurring_amount__c,
            'start_date__c': sub.start_date__c.isoformat(),
            'status__c': sub.status__c
        } for sub in subscriptions.items],
        'total_count': subscriptions.total
    })

@app.route('/v1/coding_test/order/<int:order_id>')
def get_order(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    return jsonify({
        'id': order.id,
        'closedate': order.closedate.isoformat(),
        'total_order_value__c': order.total_order_value__c,
        'parent_subscription_id__c': order.parent_subscription_id__c
    })

@app.route('/v1/coding_test/orders/<int:subscription_id>/<int:page_number>')
def get_subscription_orders(subscription_id, page_number):
    per_page = request.args.get('per_page', default=10, type=int)
    
    orders = Order.query.filter_by(parent_subscription_id__c=subscription_id).paginate(
        page=page_number,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'orders': [{
            'id': order.id,
            'closedate': order.closedate.isoformat(),
            'total_order_value__c': order.total_order_value__c,
            'parent_subscription_id__c': order.parent_subscription_id__c
        } for order in orders.items],
        'total_count': orders.total
    })

@app.route('/v1/coding_test/statistics')
def get_statistics():
    total = Subscription.query.count()
    active = Subscription.query.filter_by(status__c='active').count()
    on_hold = Subscription.query.filter_by(status__c='on-hold').count()
    canceled = Subscription.query.filter_by(status__c='canceled').count()
    
    # Calculate average subscription length
    avg_length = db.session.query(
        func.avg(
            func.julianday(Subscription.end_date__c) - func.julianday(Subscription.start_date__c)
        )
    ).filter(Subscription.end_date__c.isnot(None)).scalar() or 0
    
    return jsonify({
        'total_subscriptions': total,
        'active_subscriptions': active,
        'on_hold_subscriptions': on_hold,
        'canceled_subscriptions': canceled,
        'average_subscription_length': round(avg_length, 2)
    })

def validate_subscription_input(data):
    required_fields = ['billing_interval__c', 'start_date__c']
    for field in required_fields:
        if not data.get(field):
            return False, f"Missing required field: {field}"
    if 'recurring_amount__c' in data and data['recurring_amount__c'] is not None:
        try:
            if float(data['recurring_amount__c']) < 0:
                return False, "recurring_amount__c must be non-negative"
        except Exception:
            return False, "recurring_amount__c must be a number"
    # Validate billing_interval__c format (e.g., '1 month', '3 months')
    parts = data['billing_interval__c'].split()
    if len(parts) != 2 or not parts[0].isdigit() or parts[1] not in ['month', 'months', 'year', 'years']:
        return False, "billing_interval__c must be like '1 month', '3 months', '1 year', etc."
    return True, None

@app.errorhandler(400)
def handle_400(e):
    return jsonify({'error': str(e)}), 400

@app.errorhandler(404)
def handle_404(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def handle_500(e):
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/v1/coding_test/subscription', methods=['POST'])
def create_subscription():
    data = request.get_json()
    valid, error = validate_subscription_input(data)
    if not valid:
        return jsonify({'error': error}), 400
    subscription = Subscription(
        billing_interval__c=data.get('billing_interval__c'),
        status__c=data.get('status__c', 'active'),
        start_date__c=datetime.fromisoformat(data.get('start_date__c')),
        end_date__c=datetime.fromisoformat(data['end_date__c']) if data.get('end_date__c') else None,
        next_payment_date__c=datetime.fromisoformat(data['next_payment_date__c']) if data.get('next_payment_date__c') else None,
        recurring_amount__c=data.get('recurring_amount__c')
    )
    db.session.add(subscription)
    db.session.commit()
    return jsonify({
        'id': subscription.id,
        'billing_interval__c': subscription.billing_interval__c,
        'status__c': subscription.status__c,
        'start_date__c': subscription.start_date__c.isoformat(),
        'end_date__c': subscription.end_date__c.isoformat() if subscription.end_date__c else None,
        'next_payment_date__c': subscription.next_payment_date__c.isoformat() if subscription.next_payment_date__c else None,
        'recurring_amount__c': subscription.recurring_amount__c
    }), 201

@app.route('/v1/coding_test/subscription/<int:subscription_id>/renew', methods=['POST'])
def renew_subscription(subscription_id):
    data = request.get_json()
    if 'success' not in data:
        return jsonify({'error': 'Missing required field: success'}), 400
    if 'total_order_value__c' in data and data['total_order_value__c'] is not None:
        try:
            if float(data['total_order_value__c']) < 0:
                return jsonify({'error': 'total_order_value__c must be non-negative'}), 400
        except Exception:
            return jsonify({'error': 'total_order_value__c must be a number'}), 400
    subscription = db.session.get(Subscription, subscription_id)
    if not subscription:
        abort(404)
    success = data.get('success', True)
    if success:
        order = Order(
            closedate=datetime.now(),
            total_order_value__c=data.get('total_order_value__c', 49.99),
            parent_subscription_id__c=subscription.id
        )
        db.session.add(order)
        db.session.commit()
        return jsonify({
            'order_created': True,
            'id': order.id,
            'closedate': order.closedate.isoformat(),
            'total_order_value__c': order.total_order_value__c,
            'parent_subscription_id__c': order.parent_subscription_id__c
        }), 201
    else:
        return jsonify({'order_created': False}), 200

@app.route('/v1/coding_test/analysis/missed-payments')
def analyze_missed_payments():
    from dateutil.relativedelta import relativedelta
    from flask import request
    as_of_str = request.args.get('as_of')
    if as_of_str:
        try:
            as_of = datetime.fromisoformat(as_of_str)
        except Exception:
            return jsonify({'error': 'Invalid as_of date format'}), 400
    else:
        as_of = datetime.now()
    subscriptions = Subscription.query.filter(
        Subscription.status__c.in_(['active', 'on-hold'])
    ).all()
    total_missed_payments = 0
    total_missed_value = 0.0
    missed_payments_details = []
    for sub in subscriptions:
        start_date = sub.start_date__c
        end_date = sub.end_date__c or as_of
        interval_parts = sub.billing_interval__c.split()
        if len(interval_parts) != 2:
            continue
        number = int(interval_parts[0])
        unit = interval_parts[1]
        expected_payments = 0
        current = start_date
        while True:
            next_billing = current
            if next_billing >= as_of:
                break
            expected_payments += 1
            if unit == 'month':
                current += relativedelta(months=number)
            elif unit == 'year':
                current += relativedelta(years=number)
            else:
                break
        actual_payments = Order.query.filter_by(
            parent_subscription_id__c=sub.id
        ).count()
        missed = expected_payments - actual_payments
        if missed > 0:
            missed_value = missed * (sub.recurring_amount__c or 0)
            total_missed_payments += missed
            total_missed_value += missed_value
            missed_payments_details.append({
                'subscription_id': sub.id,
                'status': sub.status__c,
                'billing_interval': sub.billing_interval__c,
                'start_date': sub.start_date__c.isoformat(),
                'expected_payments': expected_payments,
                'actual_payments': actual_payments,
                'missed_payments': missed,
                'missed_value': missed_value
            })
    return jsonify({
        'total_missed_payments': total_missed_payments,
        'total_missed_value': round(total_missed_value, 2),
        'details': missed_payments_details
    })

@app.route('/v1/coding_test/subscription/<int:subscription_id>')
def get_subscription_detail(subscription_id):
    sub = db.session.get(Subscription, subscription_id)
    if not sub:
        abort(404)
    return jsonify({
        'id': sub.id,
        'billing_interval__c': sub.billing_interval__c,
        'end_date__c': sub.end_date__c.isoformat() if sub.end_date__c else None,
        'next_payment_date__c': sub.next_payment_date__c.isoformat() if sub.next_payment_date__c else None,
        'recurring_amount__c': sub.recurring_amount__c,
        'start_date__c': sub.start_date__c.isoformat(),
        'status__c': sub.status__c
    })

@app.route('/healthz')
def health_check():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 