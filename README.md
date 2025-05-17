# Subscription Management API Thing

A hurried Flask-based API for managing subscriptions and orders, built with SQLite, Jinja templates, Tailwind CSS, and Chart.js.

## Features

- **Subscription Management**: Create, list, and manage subscriptions.
- **Order Management**: Track orders associated with subscriptions.
- **Analytics**: Analyze missed payments and subscription statistics.
- **Authentication**: Token-based authentication for secure API access.
- **Rate Limiting**: Protect against abuse with rate limits.
- **OpenAPI Documentation**: Auto-generated Swagger UI at `/docs`.
- **Health Check**: `/healthz` endpoint for deployment readiness.

## Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd clearhear
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file**:
   ```
   API_TOKEN=supersecrettoken
   FLASK_ENV=production
   ```

5. **Initialize the database**:
   ```bash
   python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

## Running the Application

### Development

```bash
python3 app.py
```

### Production (Docker)

```bash
docker build -t clearhear .
docker run -p 5000:5000 clearhear
```

## Testing

Run the tests with:

```bash
python3 -m pytest tests/test_app.py -v
```

## API Documentation

- **Swagger UI**: Visit `/docs` for interactive API documentation.
- **Health Check**: `/healthz` returns `{"status": "ok"}` if the app is healthy.

## Security

- **Authentication**: All API endpoints (except `/healthz` and `/docs`) require a valid `Authorization: Bearer <API_TOKEN>` header.
- **Rate Limiting**: 100 requests per hour per IP address.

## License

[MIT](LICENSE)

## 🚀 Deployment & Production Usage

### Run with Docker

1. **Build the Docker image:**
   ```sh
   docker build -t clearhear .
   ```
2. **Run the container:**
   ```sh
   docker run -d -p 5000:5000 --name clearhear_app clearhear
   ```
3. **Access the app:**
   - App: http://localhost:5000
   - API docs: http://localhost:5000/docs

4. **Stop the app:**
   ```sh
   docker stop clearhear_app
   ```
5. **View logs:**
   ```sh
   docker logs clearhear_app
   ```

---

## 🛡️ Production Notes
- The Docker image uses Gunicorn for production WSGI serving.
- For rate limiting in production, configure a persistent backend (e.g., Redis) as per [Flask-Limiter docs](https://flask-limiter.readthedocs.io#configuring-a-storage-backend).
- Set a strong `API_TOKEN` in your environment or `.env` file.
- For custom domains or HTTPS, use a reverse proxy (e.g., Nginx, Caddy).

--- 
