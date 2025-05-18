from fastapi import FastAPI, HTTPException, Depends
from typing import Dict, List
import logging
import asyncio
from app.api_client import AudicusAPIClient
from app.analytics import calculate_subscription_stats, calculate_missed_payments
from app.models import AnalyticsResponse, Order

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Audicus Subscription Analytics")

# Dependency to get API client
async def get_api_client():
    client = AudicusAPIClient()
    try:
        yield client
    finally:
        await client.close()

@app.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(api_client: AudicusAPIClient = Depends(get_api_client)):
    """
    Get subscription analytics including:
    - Total, active, on-hold, and cancelled subscriptions
    - Average subscription length
    - Number and value of missed payments (from on-hold or active subscriptions)
    """
    try:
        # Fetch all subscriptions
        logger.info("Fetching subscriptions...")
        subscriptions = await api_client.get_subscriptions()
        
        if not subscriptions:
            raise HTTPException(status_code=404, detail="No subscriptions found")
        
        logger.info(f"Found {len(subscriptions)} subscriptions")
        
        # Calculate subscription stats
        subscription_stats = calculate_subscription_stats(subscriptions)
        
        # Fetch orders for each subscription concurrently
        logger.info("Fetching orders for each subscription...")
        all_orders: Dict[int, List[Order]] = {}
        
        async def fetch_orders_for_subscription(sub_id: int):
            orders = await api_client.get_subscription_orders(sub_id)
            if orders:
                all_orders[sub_id] = orders
        
        # Create tasks for fetching orders
        tasks = []
        for sub in subscriptions:
            task = fetch_orders_for_subscription(sub.id)
            tasks.append(task)
        
        # Execute all tasks concurrently
        await asyncio.gather(*tasks)
        
        logger.info(f"Fetched orders for {len(all_orders)} subscriptions")
        
        # Calculate missed payments
        missed_payment_stats = calculate_missed_payments(subscriptions, all_orders)
        
        # Return the combined analytics
        return AnalyticsResponse(
            subscription_stats=subscription_stats,
            missed_payment_stats=missed_payment_stats
        )
    
    except HTTPException as http_exc:
        # Specifically catch HTTPException and re-raise it as is
        logger.error(f"HTTPException in get_analytics: {http_exc.status_code} - {http_exc.detail}")
        raise http_exc
        
    except Exception as e:
        # For other exceptions, return a 500 status code
        logger.error(f"Error getting analytics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))