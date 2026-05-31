import json
import logging
import os
import signal
import time

import redis
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from psycopg_pool import ConnectionPool
from pythonjsonlogger.json import JsonFormatter

from opentelemetry import propagate, trace
from opentelemetry.context import attach, detach
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


POSTGRES_DSN = os.environ["POSTGRES_DSN"]
REDIS_URL = os.environ["REDIS_URL"]
MATCH_QUEUE_KEY = "matches:pending"

WORKER_MATCHES_CONSUMED = Counter(
    "worker_matches_consumed_total",
    "Total match jobs consumed by the worker",
)

WORKER_MATCH_PROCESSING_SECONDS = Histogram(
    "worker_match_processing_seconds",
    "Time spent processing one match job",
)

WORKER_MATCH_FAILURES = Counter(
    "worker_match_failures_total",
    "Total worker match processing failures",
    ["reason"],
)

QUEUE_DEPTH = Gauge(
    "matchmaking_queue_depth",
    "Current Redis matchmaking queue depth",
)

def configure_logging() -> None:
    handler = logging.StreamHandler()
    formatter = JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(os.getenv("LOG_LEVEL", "INFO"))


def configure_tracing() -> None:
    resource = Resource.create({
        "service.name": os.getenv("OTEL_SERVICE_NAME", "worker")
    })

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317"),
        insecure=True,
    )

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

configure_logging()
configure_tracing()

logger = logging.getLogger("worker")
tracer = trace.get_tracer("worker")

RedisInstrumentor().instrument()
PsycopgInstrumentor().instrument()

def parse_match_payload(raw_payload: str) -> dict:
    payload = json.loads(raw_payload)

    return {
        "match_id": str(payload["match_id"]),
        "request_id": payload.get("request_id"),
        "match_request_id": payload.get("match_request_id"),
        "player_id": payload.get("player_id"),
        "traceparent": payload.get("traceparent"),
        "tracestate": payload.get("tracestate"),
    }


def log_context(payload: dict) -> dict:
    return {
        "request_id": payload.get("request_id"),
        "match_request_id": payload.get("match_request_id"),
        "player_id": payload.get("player_id"),
        "match_id": payload.get("match_id"),
    }


def set_span_attributes(span, fields: dict) -> None:
    for key, value in fields.items():
        if value is not None:
            span.set_attribute(key, value)

running = True


def stop(_signum, _frame):
    global running
    running = False


def mark_processed(pool: ConnectionPool, match_id: str, fields: dict) -> bool:
    with tracer.start_as_current_span("db.match_ready") as span:
        set_span_attributes(span, fields)

        with pool.connection() as conn, conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE matches SET status = %s WHERE id = %s",
                    ("ready", match_id),
                )

                found = cur.rowcount == 1
                span.set_attribute("match.found", found)
                return found


def main() -> int:
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    start_http_server(9091)

    rds = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    pool = ConnectionPool(POSTGRES_DSN, min_size=1, max_size=4)

    logger.info("worker.started", extra={"queue": MATCH_QUEUE_KEY})
    try:
        while running:
            item = rds.brpop(MATCH_QUEUE_KEY, timeout=5)
            QUEUE_DEPTH.set(rds.llen(MATCH_QUEUE_KEY))

            if item is None:
                continue

            _, raw_payload = item

            try:
                payload = parse_match_payload(raw_payload)
            except Exception:
                WORKER_MATCH_FAILURES.labels("invalid_payload").inc()
                logger.exception(
                    "worker.payload_invalid",
                    extra={"raw_payload": raw_payload},
                )
                continue

            fields = log_context(payload)

            carrier = {}
            if payload.get("traceparent"):
                carrier["traceparent"] = payload["traceparent"]
            if payload.get("tracestate"):
                carrier["tracestate"] = payload["tracestate"]

            parent_context = propagate.extract(carrier)
            token = attach(parent_context)

            try:
                with tracer.start_as_current_span("worker.consume_match") as span:
                    set_span_attributes(span, fields)

                    logger.info("worker.match_received", extra=fields)

                    with WORKER_MATCH_PROCESSING_SECONDS.time():
                        processed = mark_processed(pool, payload["match_id"], fields)

                    WORKER_MATCHES_CONSUMED.inc()

                    if processed:
                        logger.info("worker.match_ready", extra=fields)
                    else:
                        WORKER_MATCH_FAILURES.labels("match_not_found").inc()
                        logger.warning("worker.match_not_found", extra=fields)

            finally:
                detach(token)
    finally:
        pool.close()
        rds.close()

    logger.info("worker.stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
