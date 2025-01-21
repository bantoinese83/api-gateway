import os
import secrets
from dotenv import load_dotenv
from consul import Consul

load_dotenv()

class Config:
    # Service URLs
    SERVICE_A_URL = os.getenv("SERVICE_A_URL", "http://localhost:8001")
    SERVICE_B_URL = os.getenv("SERVICE_B_URL", "http://localhost:8002")

    # API Gateway settings
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", 'false').lower() == 'true'

    # Authentication settings
    JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

    # Rate Limiting
    RATE_LIMIT = os.getenv("RATE_LIMIT", "100/minute") # eg, 100/minute or 1000/hour

    # Jaeger Tracing
    JAEGER_HOST = os.getenv("JAEGER_HOST", "localhost")
    JAEGER_PORT = int(os.getenv("JAEGER_PORT", 14250))

    # Health Check
    HEALTH_CHECK_PATH = os.getenv("HEALTH_CHECK_PATH", "/health")
    HEALTH_CHECK_SERVICE_A = os.getenv("HEALTH_CHECK_SERVICE_A", "/health")
    HEALTH_CHECK_SERVICE_B = os.getenv("HEALTH_CHECK_SERVICE_B", "/health")

    # Redis URL
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    def __init__(self):
        self.consul = Consul()

    def discover_services(self):
        index, services = self.consul.catalog.services()
        service_a = services.get('service-a')
        service_b = services.get('service-b')
        if service_a:
            self.SERVICE_A_URL = f"http://{service_a[0]['ServiceAddress']}:{service_a[0]['ServicePort']}"
        if service_b:
            self.SERVICE_B_URL = f"http://{service_b[0]['ServiceAddress']}:{service_b[0]['ServicePort']}"

config = Config()
config.discover_services()
