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
from core.database import engine, Base, seed_roles
from contextlib import asynccontextmanager
from services.shows_consumer import start_consumer_thread
import time
import requests
from kafka import KafkaProducer

def wait_for_elasticsearch():
    es_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            response = requests.get(f"{es_url}/_cluster/health", timeout=5)
            if response.status_code == 200:
                print("Elasticsearch is ready")
                return True
        except Exception as e:
            print(f"Waiting for Elasticsearch... (attempt {i+1}/{max_retries})")
            time.sleep(retry_interval)
    
    raise Exception("Elasticsearch failed to start within expected time")


def wait_for_kafka():
    kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=kafka_bootstrap,
                request_timeout_ms=5000
            )
            producer.close()
            print("Kafka is ready")
            return True
        except Exception as e:
            print(f"Waiting for Kafka... (attempt {i+1}/{max_retries})")
            time.sleep(retry_interval)
    
    raise Exception("Kafka failed to start within expected time")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting FastAPI application...")
    
    print("Checking dependencies...")
    wait_for_elasticsearch()
    wait_for_kafka()
    
    print("All dependencies are ready!")

    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Seed roles table
    seed_roles()
    start_consumer_thread()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(show.router)


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
