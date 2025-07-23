from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry import trace
import sqlalchemy as sa
import redis.asyncio as redis
import os
from api import auth, show
from core.database import engine, Base
from contextlib import asynccontextmanager
from services.shows_consumer import start_consumer_thread


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_consumer_thread()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(show.router)

Base.metadata.create_all(bind=engine)

# Prometheus metrics
REQUEST_COUNT = Counter('request_count', 'Total HTTP requests')


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    REQUEST_COUNT.inc()
    response = await call_next(request)
    return response


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def root():
    return {"message": "Hello world, FastAPI!"}


# Redis setup
REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.from_url(REDIS_URL)

# OpenTelemetry setup
resource = Resource(attributes={SERVICE_NAME: "fastapi-app"})
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)

# Instrumentations
FastAPIInstrumentor.instrument_app(app)
RedisInstrumentor().instrument()
SQLAlchemyInstrumentor().instrument(engine=engine)

# Prometheus metrics exporter
metric_reader = PrometheusMetricReader()
meter_provider = MeterProvider(
    resource=resource, metric_readers=[metric_reader])
