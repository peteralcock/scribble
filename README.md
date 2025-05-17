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