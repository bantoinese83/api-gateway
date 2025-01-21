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

## License

This project is licensed under the MIT License.

## Running All Services

You can use the `run_all.sh` script to start and stop all services.

### Start All Services

