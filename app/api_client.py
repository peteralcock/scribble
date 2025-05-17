import httpx
from typing import List, Dict, Optional
import logging
from datetime import datetime
from app.models import Subscription, Order

logger = logging.getLogger(__name__)

class AudicusAPIClient:
    BASE_URL = "https://jungle.audicus.com/v1/coding_test"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()
    
    async def get_subscriptions(self, per_page: int = 100) -> List[Subscription]:
        """
        Fetch all subscriptions from the API with pagination.
        """
        all_subscriptions = []
        page = 1
        more_pages = True
        
        while more_pages:
            try:
                url = f"{self.BASE_URL}/subscriptions/{page}?per_page={per_page}"
                response = await self.client.get(url)
                response.raise_for_status()
                
                data = response.json()
                subscriptions = data.get("subscriptions", [])
                
                if not subscriptions:
                    more_pages = False
                else:
                    # Convert string dates to datetime objects
                    for sub in subscriptions:
                        for date_field in ["end_date__c", "next_payment_date__c", "start_date__c"]:
                            if sub.get(date_field):
                                try:
                                    sub[date_field] = datetime.fromisoformat(sub[date_field].replace("Z", "+00:00"))
                                except (ValueError, AttributeError):
                                    sub[date_field] = None
                    
                    all_subscriptions.extend([Subscription(**sub) for sub in subscriptions])
                    page += 1
                    
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching subscriptions page {page}: {e}")
                more_pages = False
            except Exception as e:
                logger.error(f"Error fetching subscriptions page {page}: {e}")
                more_pages = False
                
        return all_subscriptions
    
    async def get_subscription_orders(self, subscription_id: int) -> List[Order]:
        """
        Fetch all orders for a specific subscription with pagination.
        """
        all_orders = []
        page = 1
        more_pages = True
        
        while more_pages:
            try:
                url = f"{self.BASE_URL}/orders/{subscription_id}/{page}"
                response = await self.client.get(url)
                response.raise_for_status()
                
                data = response.json()
                orders = data.get("orders", [])
                
                if not orders:
                    more_pages = False
                else:
                    # Convert string dates to datetime objects
                    for order in orders:
                        if order.get("closedate"):
                            order["closedate"] = datetime.fromisoformat(order["closedate"].replace("Z", "+00:00"))
                    
                    all_orders.extend([Order(**order) for order in orders])
                    page += 1
                    
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching orders for subscription {subscription_id}, page {page}: {e}")
                more_pages = False
            except Exception as e:
                logger.error(f"Error fetching orders for subscription {subscription_id}, page {page}: {e}")
                more_pages = False
                
        return all_orders
        
    async def get_order(self, order_id: int) -> Optional[Order]:
        """
        Fetch a specific order by ID.
        """
        try:
            url = f"{self.BASE_URL}/order/{order_id}"
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            order_data = data.get("order")
            
            if order_data and order_data.get("closedate"):
                order_data["closedate"] = datetime.fromisoformat(order_data["closedate"].replace("Z", "+00:00"))
                
            return Order(**order_data) if order_data else None
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching order {order_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {e}")
            return None