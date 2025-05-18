# Audicus Subscription Analytics API

This API service fetches, parses, and analyzes subscription and order data from the Audicus API.

## Requirements

- Python 3.8+
- Required packages listed in requirements.txt

## Installation

1. Clone or unzip this repository
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Running the Application

To run the application, use the following command from the project root directory:

```bash
python application.py
```

The API will be available at http://localhost:8000

## API Endpoints

### GET /analytics

Returns analytics about Audicus subscriptions, including:
- Total, active, on-hold, and cancelled subscriptions
- Average subscription length in days
- Number and value of missed payments (from on-hold or active subscriptions)

Example response:
```json
{
  "subscription_stats": {
    "total_subscriptions": 100,
    "active_subscriptions": 75,
    "on_hold_subscriptions": 10,
    "cancelled_subscriptions": 15,
    "average_subscription_length_days": 187.5
  },
  "missed_payment_stats": {
    "missed_payments_count": 23,
    "missed_payments_value": 1250.75
  }
}
```

## Documentation

Auto-generated API documentation is available at:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Project Structure

```
audicus_analytics/
├── app/
│   ├── __init__.py
│   ├── api_client.py     # Handles API communication
│   ├── analytics.py      # Analytics calculation logic
│   ├── main.py           # FastAPI application definition
│   └── models.py         # Data models
├── requirements.txt
├── README.md
└── application.py        # Entry point
```

## Notes

### API Limitations & Potential Improvements

1. The service would benefit from bulk endpoints to fetch orders for multiple subscriptions at once
2. Current implementation handles pagination manually by fetching all pages
3. Concurrent requests are used to improve performance when fetching orders
4. Error handling includes logging but could be expanded with more detailed error responses
5. Date formats require normalization to handle ISO-8601 timestamps correctly

## Assignment Questions & Reflections

Here are responses to the questions posed in the assignment:

### 1. What further information would you like from the API, if any?

While the provided API endpoints and data fields were largely sufficient for the tasks, some additional information could be beneficial for deeper analysis or more robust error handling:

* **Reason codes for 'on-hold' status:** If a subscription is `on-hold` due to a failed charge, having a reason code (e.g., insufficient funds, card expired, generic failure) could help in segmenting these issues or understanding payment failure patterns.
* **Explicit `total_pages` or `has_next_page` in paginated responses:** For paginated endpoints like `/subscriptions` and `/orders`, including a `total_pages` count or a boolean `has_next_page` field (or a direct `next_page_url`) in the API response would make client-side pagination slightly more explicit than relying solely on checking for an empty list of results.
* **Timestamp for status changes:** Knowing when a subscription's status last changed (e.g., when it moved to `on-hold` or `canceled`) could enable more precise time-based analytics.

### 2. What limitations or errors did you find, if any?

During development and testing with the provided API, the following limitations and characteristics were noted:

* **Lack of Bulk Endpoints for Orders:** The most significant limitation is the absence of an endpoint to fetch orders for multiple subscriptions in a single request. To get all orders, the current service needs to make a separate series of paginated calls for each subscription (N+1 problem for fetching orders associated with a list of subscriptions). This increases overall data retrieval time and the number of API calls.
* **Date Format Requiring Client Normalization:** Dates are provided as ISO-8601 strings ending in 'Z' (e.g., `"2024-01-01T00:00:00Z"`). This is a standard format but requires consistent client-side parsing into timezone-aware datetime objects (UTC, in this case) for accurate calculations. This was handled in the API client.
* **No Explicit Indication of Last Page:** As mentioned above, client-side pagination relies on receiving an empty list of items to determine the end of a paginated resource, rather than a specific field indicating the last page.
* **`order/{order_id}` Endpoint:** The `https://jungle.audicus.com/v1/coding_test/order/{order_id}` endpoint was noted. While available, it was not directly utilized in the primary `/analytics` service logic, as the requirement was to analyze orders in the context of their parent subscriptions (for which `orders/{subscription_id}/{page_number}` was more suitable).

No outright blocking errors were encountered with the API itself during the development of this project. The API behaved consistently according to the described endpoints.

### 3. What changes would you make to improve the API, if any?

Based on the experience building this service, the following improvements to the external Audicus API would be beneficial:

* **Introduce a Bulk Order Fetch Endpoint:** This is the most impactful suggested change. An endpoint like `GET /v1/coding_test/orders-bulk?subscription_ids=1,2,3...` or `POST /v1/coding_test/orders-bulk` (with a list of subscription IDs in the request body) would dramatically improve efficiency by reducing the number of API calls needed.
* **Provide Clearer End-of-Life Data for Subscriptions:**
    * Ensure `end_date__c` is always populated by the API when a subscription status moves to `canceled`. While the client can infer an end date of 'now' for analytical purposes if it's missing, having this explicitly set by the API would be more definitive.
* **Enhance Paginated Responses:** Include metadata like `total_items`, `total_pages`, and direct `next_page_url` / `previous_page_url` links in paginated responses to simplify client-side iteration.
* **More Granular Error Information:** For failed requests, especially for actions like payment processing (which leads to `on-hold`), providing more detailed error codes or messages within the API response body (beyond standard HTTP status codes) could aid in debugging and client-side error handling.
