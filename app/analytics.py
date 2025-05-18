from typing import List, Dict, Tuple
from datetime import datetime, timedelta, timezone
import re
from dateutil.relativedelta import relativedelta
from app.models import Subscription, Order, SubscriptionStats, MissedPaymentStats

def calculate_subscription_stats(subscriptions: List[Subscription]) -> SubscriptionStats:
    """
    Calculate subscription statistics based on the list of subscriptions.
    """
    total_subscriptions = len(subscriptions)
    active_subscriptions = sum(1 for sub in subscriptions if sub.status__c == "active")
    on_hold_subscriptions = sum(1 for sub in subscriptions if sub.status__c == "on-hold")
    cancelled_subscriptions = sum(1 for sub in subscriptions if sub.status__c == "canceled")
    
    # Calculate average subscription length
    now = datetime.now(timezone.utc)
    subscription_lengths = []
    
    for sub in subscriptions:
        start_date = sub.start_date__c
        end_date = sub.end_date__c if sub.end_date__c else now if sub.status__c == "canceled" else None
        
        if start_date and end_date:
            subscription_length = (end_date - start_date).days
            subscription_lengths.append(subscription_length)
    
    avg_subscription_length = sum(subscription_lengths) / len(subscription_lengths) if subscription_lengths else 0
    
    return SubscriptionStats(
        total_subscriptions=total_subscriptions,
        active_subscriptions=active_subscriptions,
        on_hold_subscriptions=on_hold_subscriptions,
        cancelled_subscriptions=cancelled_subscriptions,
        average_subscription_length_days=avg_subscription_length
    )

def parse_billing_interval(interval_str: str) -> Tuple[int, str]:
    """
    Parse billing interval string like "3 months" into (3, "months").
    """
    match = re.match(r"(\d+)\s+(\w+)", interval_str)
    if match:
        value = int(match.group(1))
        unit = match.group(2).lower()
        # Normalize unit to singular
        if unit.endswith('s') and unit != 'months':
            unit = unit[:-1]
        return value, unit
    return 1, "month"  # Default to 1 month if parsing fails

def calculate_missed_payments(subscriptions: List[Subscription], all_orders: Dict[int, List[Order]]) -> MissedPaymentStats:
    """
    Calculate the number and value of missed payments from on-hold or active subscriptions.
    """
    now = datetime.now(timezone.utc)
    missed_payments_count = 0
    missed_payments_value = 0.0
    
    for sub in subscriptions:
        if sub.status__c not in ["active", "on-hold"]:
            continue
            
        # Skip subscriptions with no recurring amount
        if not sub.recurring_amount__c:
            continue
            
        # Get orders for this subscription
        sub_orders = all_orders.get(sub.id, [])
        
        # Sort orders by date
        sub_orders.sort(key=lambda x: x.closedate)
        
        # Parse billing interval
        interval_value, interval_unit = parse_billing_interval(sub.billing_interval__c)
        
        # Calculate expected number of orders based on start date and billing interval
        expected_dates = []
        current_date = sub.start_date__c
        
        while current_date <= now:
            expected_dates.append(current_date)
            
            # Calculate the next expected date based on the billing interval
            if interval_unit == "month" or interval_unit == "months":
                current_date += relativedelta(months=interval_value)
            elif interval_unit == "year" or interval_unit == "years":
                current_date += relativedelta(years=interval_value)
            elif interval_unit == "day" or interval_unit == "days":
                current_date += timedelta(days=interval_value)
            elif interval_unit == "week" or interval_unit == "weeks":
                current_date += timedelta(weeks=interval_value)
            else:
                # Default to monthly if unit is unknown
                current_date += relativedelta(months=interval_value)
        
        # Count how many expected dates don't have a corresponding order
        # Allow for a 7-day window for each expected date
        for expected_date in expected_dates:
            order_found = False
            for order in sub_orders:
                # If an order exists within 7 days of the expected date, count it as fulfilled
                if abs((order.closedate - expected_date).days) <= 7:
                    order_found = True
                    break
            
            if not order_found:
                missed_payments_count += 1
                missed_payments_value += sub.recurring_amount__c or 0
    
    return MissedPaymentStats(
        missed_payments_count=missed_payments_count,
        missed_payments_value=missed_payments_value
    )