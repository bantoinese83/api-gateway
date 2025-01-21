import json
import logging
import time
from typing import Callable

from fastapi import Request
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.propagate import inject
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes

from config.config import config

# Initialize Jaeger Tracer
resource = Resource(attributes={
    ResourceAttributes.SERVICE_NAME: "api-gateway",
    ResourceAttributes.DEPLOYMENT_ENVIRONMENT: 'development',
})
trace_provider = TracerProvider(resource=resource)
jaeger_exporter = JaegerExporter(
    collector_endpoint=f"http://{config.JAEGER_HOST}:{config.JAEGER_PORT}/api/traces",
)
trace_processor = BatchSpanProcessor(jaeger_exporter)
trace_provider.add_span_processor(trace_processor)
tracer = trace.get_tracer(__name__)


async def logging_middleware(request: Request, call_next):
    """
    Logs request and response info.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logging.info(
        f"Request: {request.method} {request.url} | Status: {response.status_code} | Process Time: {process_time:.4f}s")
    return response


async def tracing_middleware(request: Request, call_next):
    """
    Creates spans for each request to be logged in a tracing engine like jaeger.
    """

    carrier = {}
    inject(carrier)
    headers = dict(request.headers)
    headers.update(carrier)
    request.scope['headers'] = [(k.encode("utf-8"), v.encode("utf-8")) for k, v in headers.items()]

    with tracer.start_as_current_span(f"{request.method} {request.url.path}") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))

        response = await call_next(request)

        span.set_attribute("http.status_code", response.status_code)
        return response


async def transform_request_middleware(request: Request, call_next: Callable):
    """
    Example of request transformation middleware. You can add more sophisticated logic here.
    """
    if request.method == "POST" and request.url.path.startswith("/service-b"):
        try:
            data = await request.json()
            if isinstance(data, dict):
                data['transformed'] = True
                request._body = json.dumps(data).encode('utf-8')

            return await call_next(request)
        except:
            return await call_next(request)

    return await call_next(request)