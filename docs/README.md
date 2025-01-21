# API Gateway ![License](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/python-3.12%2B-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-API%20Gateway-green) ![Redis](https://img.shields.io/badge/Redis-6.2.5-red) ![Jaeger](https://img.shields.io/badge/Jaeger-1.41.0-orange) ![Build](https://img.shields.io/github/actions/workflow/status/bantoinese83/api-gateway/ci.yml) ![Coverage](https://img.shields.io/codecov/c/github/bantoinese83/api-gateway)

🚀 This project is an API Gateway built using FastAPI. It forwards requests to downstream services and includes features
such as rate limiting, authentication, logging, and tracing.

## Features

- 🚦 **Rate Limiting**: Limits the number of requests to prevent abuse.
- 🔒 **Authentication**: JWT-based authentication to secure endpoints.
- 📜 **Logging**: Logs request and response information.
- 🔍 **Tracing**: Traces requests using Jaeger for distributed tracing.
- 🩺 **Health Checks**: Checks the health of downstream services.

## Requirements

- 🐍 Python 3.12+
- 🛠️ Redis
- 🕵️ Jaeger
- 🗄️ Consul

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/bantoinese83/api-gateway.git
    cd api-gateway
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv .venv
    source .venv/bin/activate
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up environment variables:
    ```sh
    cp docs/.env.example docs/.env
    ```

5. Update the `.env` file with your configuration.

## Running the Services

1. Start Redis:
    ```sh
    brew services start redis
    ```

2. Start Jaeger:
    ```sh
    jaeger-all-in-one &
    ```

3. Start Consul:
    ```sh
    consul agent -dev -bind=127.0.0.1 -client=127.0.0.1 &
    ```

4. Start the downstream services:
    ```sh
    cd service-a
    uvicorn main:app --host 0.0.0.0 --port 8001 &
    cd ../service-b
    uvicorn main:app --host 0.0.0.0 --port 8002 &
    cd ..
    ```

5. Start the API Gateway:
    ```sh
    uvicorn src.main:app --host 0.0.0.0 --port 8080
    ```

### Start All Services

```sh
  ./run_all.sh
```

### Stop All Services

```sh
  ./run_all.sh stop
```

## Running Tests

1. Install test dependencies:
    ```sh
    pip install pytest pytest-asyncio
    ```

2. Run the tests:
    ```sh
    pytest
    ```

## Usage

### Health Check

| Method | Endpoint |
|--------|----------|
| GET    | /health  |

### Read Item

| Method | Endpoint         |
|--------|------------------|
| GET    | /items/{item_id} |

### Gateway Endpoints

| Method | Endpoint             |
|--------|----------------------|
| GET    | /service-a/some-path |
| POST   | /service-a/some-path |
| PUT    | /service-a/some-path |
| DELETE | /service-a/some-path |
| PATCH  | /service-a/some-path |

## Configuration

Configuration is managed through environment variables. Refer to the `docs/.env` file for available settings.

## Middleware

### Logging Middleware

The logging middleware logs request and response information, including method, URL, status code, headers, and body (for POST, PUT, and PATCH requests). It also logs the processing time for each request.

### Tracing Middleware

The tracing middleware creates spans for each request to be logged in a tracing engine like Jaeger. It sets attributes such as HTTP method, URL, and status code.

### Transform Request Middleware

The transform request middleware is an example of request transformation middleware. It adds a `transformed` field to the request body for POST requests to `/service-b`.

## Security

### Authentication

The authentication function authenticates the JWT token provided in the `Authorization` header. It raises an HTTP 401 error if the token is missing, expired, or invalid.

## Utility Functions

### Forward Request

The `forward_request` function forwards the request to the specified URL. It includes retry logic and a circuit breaker to handle failures. The response is cached for future requests.

### Check Service Health

The `check_service_health` function performs a health check for a given service by sending a GET request to the service's health endpoint.

## Project Structure

```
api-gateway/
├── config/
│   └── config.py
├── core/
│   ├── middleware.py
│   ├── security.py
│   └── utils.py
├── docs/
│   ├── .env.example
│   └── README.md
├── services/
│   ├── service_a/
│   │   └── main.py
│   └── service_b/
│       └── main.py
├── tests/
│   ├── conftest.py
│   └── test_main.py
├── .env
├── .gitignore
├── main.py
├── pytest.ini
├── requirements.txt
└── run_all.sh
```

- `config/`: Contains configuration files.
- `core/`: Contains core functionality such as middleware, security, and utility functions.
- `docs/`: Contains documentation files.
- `services/`: Contains downstream services.
- `tests/`: Contains test files.
- `.env`: Environment variables file.
- `.gitignore`: Git ignore file.
- `main.py`: Main entry point for the API Gateway.
- `pytest.ini`: Pytest configuration file.
- `requirements.txt`: Python dependencies file.
- `run_all.sh`: Script to start and stop all services.

## Contributing

We welcome contributions to the project! Please follow these guidelines when submitting issues and pull requests:

1. Fork the repository and create a new branch for your feature or bugfix.
2. Write tests for your changes.
3. Ensure all tests pass.
4. Submit a pull request with a clear description of your changes.

## Deployment

To deploy the API Gateway to a production environment, follow these steps:

1. Set up a production-ready environment with the required dependencies (Python, Redis, Jaeger, Consul).
2. Configure environment variables in the `.env` file.
3. Use a process manager like `supervisord` or `systemd` to manage the API Gateway process.
4. Set up a reverse proxy (e.g., Nginx) to handle incoming requests and forward them to the API Gateway.
5. Monitor the API Gateway using tools like Prometheus and Grafana for metrics and alerts.
