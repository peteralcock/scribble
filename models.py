from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    billing_interval__c = db.Column(db.String(50))
    end_date__c = db.Column(db.DateTime, nullable=True)
    next_payment_date__c = db.Column(db.DateTime, nullable=True)
    recurring_amount__c = db.Column(db.Float, nullable=True)
    start_date__c = db.Column(db.DateTime, nullable=False)
    status__c = db.Column(db.String(20), nullable=False)
    
    orders = db.relationship('Order', backref='subscription', lazy=True)

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    closedate = db.Column(db.DateTime, nullable=False)
    total_order_value__c = db.Column(db.Float, nullable=False)
    parent_subscription_id__c = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False) 