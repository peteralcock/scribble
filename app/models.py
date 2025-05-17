from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Subscription(BaseModel):
    id: int
    billing_interval__c: str
    end_date__c: Optional[datetime] = None
    next_payment_date__c: Optional[datetime] = None
    recurring_amount__c: Optional[float] = None
    start_date__c: datetime
    status__c: str

class Order(BaseModel):
    id: int
    closedate: datetime
    total_order_value__c: float
    parent_subscription_id__c: int

class SubscriptionStats(BaseModel):
    total_subscriptions: int
    active_subscriptions: int
    on_hold_subscriptions: int
    cancelled_subscriptions: int
    average_subscription_length_days: float
    
class MissedPaymentStats(BaseModel):
    missed_payments_count: int
    missed_payments_value: float

class AnalyticsResponse(BaseModel):
    subscription_stats: SubscriptionStats
    missed_payment_stats: Optional[MissedPaymentStats] = None
