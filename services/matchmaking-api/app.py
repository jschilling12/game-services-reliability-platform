import os
import uuid
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, Field

import json
import logging
import time

from prometheus_client import Counter, Gauge, Histogram, make_asgi_app
from pythonjsonlogger.json import JsonFormatter

from opentelemetry import propagate, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

POSTGRES_DSN = os.environ["POSTGRES_DSN"]
REDIS_URL = os.environ["REDIS_URL"]
MATCH_QUEUE_KEY = "matches:pending"
RANK_WINDOW = 50
MATCH_QUEUE_KEY = "matches:pending"
RANK_WINDOW = 50

HTTP_REQUESTS = Counter(
    "matchmaking_http_requests_total",
    "Total HTTP requests handled by matchmaking API",
    ["method", "path", "status"],
)

HTTP_LATENCY = Histogram(
    "matchmaking_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)

HTTP_ERRORS = Counter(
    "matchmaking_http_errors_total",
    "Total HTTP 5xx responses from matchmaking API",
    ["method", "path"],
)

JOIN_REQUESTS = Counter(
    "matchmaking_join_requests_total",
    "Total matchmaking join requests",
    ["result"],
)

MATCHES_CREATED = Counter(
    "matchmaking_matches_created_total",
    "Total matches created by matchmaking API",
)

QUEUE_DEPTH = Gauge(
    "matchmaking_queue_depth",
    "Current Redis matchmaking queue depth",
)


class JoinRequest(BaseModel):
    player_id: str = Field(min_length=1)
    rank: int = Field(ge=0)


class JoinResponse(BaseModel):
    queued: bool
    match_id: str | None

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
        "service.name": os.getenv("OTEL_SERVICE_NAME", "matchmaking-api")
    })

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317"),
        insecure=True,
    )

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pg = ConnectionPool(POSTGRES_DSN, min_size=1, max_size=8, kwargs={"row_factory": dict_row})
    app.state.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    try:
        yield
    finally:
        app.state.pg.close()
        app.state.redis.close()

configure_logging()
configure_tracing()

logger = logging.getLogger("matchmaking-api")
tracer = trace.get_tracer("matchmaking-api")


app = FastAPI(lifespan=lifespan)

app.mount("/metrics", make_asgi_app())

FastAPIInstrumentor.instrument_app(app)
RedisInstrumentor().instrument()
PsycopgInstrumentor().instrument()

@app.middleware("http")
async def request_context(request: Request, call_next):
    start = time.perf_counter()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    method = request.method
    path = request.url.path

    try:
        response = await call_next(request)
    except Exception:
        duration = time.perf_counter() - start
        HTTP_REQUESTS.labels(method, path, "500").inc()
        HTTP_ERRORS.labels(method, path).inc()
        HTTP_LATENCY.labels(method, path).observe(duration)

        logger.exception(
            "http.request.failed",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "duration_ms": round(duration * 1000, 2),
            },
        )

        response = JSONResponse(
            status_code=500,
            content={"detail": "internal server error"},
        )

    duration = time.perf_counter() - start
    status = str(response.status_code)

    HTTP_REQUESTS.labels(method, path, status).inc()
    HTTP_LATENCY.labels(method, path).observe(duration)

    if response.status_code >= 500:
        HTTP_ERRORS.labels(method, path).inc()

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "http.request.completed",
        extra={
            "request_id": request_id,
            "method": method,
            "path": path,
            "status": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        },
    )

    return response


@app.post("/queue/join", response_model=JoinResponse)
async def join_queue(req: JoinRequest, request: Request) -> JoinResponse:
    pool: ConnectionPool = request.app.state.pg
    rds: redis.Redis = request.app.state.redis

    with pool.connection() as conn, conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO queue (player_id, rank) VALUES (%s, %s)",
                (req.player_id, req.rank),
            )
            cur.execute(
                """
                SELECT id, player_id, rank
                FROM queue
                WHERE rank BETWEEN %s AND %s
                ORDER BY created_at
                LIMIT 2
                """,
                (req.rank - RANK_WINDOW, req.rank + RANK_WINDOW),
            )
            candidates = cur.fetchall()

            if len(candidates) < 2:
                return JoinResponse(queued=True, match_id=None)

            a, b = candidates[0], candidates[1]
            cur.execute("DELETE FROM queue WHERE id IN (%s, %s)", (a["id"], b["id"]))
            match_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO matches (id, player_a, player_b) VALUES (%s, %s, %s)",
                (match_id, a["player_id"], b["player_id"]),
            )

    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    match_request_id = str(uuid.uuid4())

    carrier: dict[str, str] = {}
    propagate.inject(carrier)

    payload = {
        "match_id": match_id,
        "request_id": request_id,
        "match_request_id": match_request_id,
        "player_id": req.player_id,
        "traceparent": carrier.get("traceparent"),
        "tracestate": carrier.get("tracestate"),
    }

    with tracer.start_as_current_span("redis.queue_push"):
        rds.lpush(MATCH_QUEUE_KEY, json.dumps(payload))
        QUEUE_DEPTH.set(rds.llen(MATCH_QUEUE_KEY))

    log_context = {
        "request_id": request_id,
        "match_request_id": match_request_id,
        "player_id": req.player_id,
        }
    logger.info("join.received", extra=log_context)

    logger.info(
        "redis.pushed",
        extra={**log_context, "match_id": match_id},
    )

    with tracer.start_as_current_span("join_queue") as span:
        span.set_attribute("request_id", request_id)
        span.set_attribute("match_request_id", match_request_id)
        span.set_attribute("player_id", req.player_id)
    
    # keep your existing DB and Redis logic inside this block

    logger.info("db.queue_inserted", extra=log_context)

    JOIN_REQUESTS.labels("queued").inc()
    QUEUE_DEPTH.set(rds.llen(MATCH_QUEUE_KEY))

    span.set_attribute("match_id", match_id)
    MATCHES_CREATED.inc()
    JOIN_REQUESTS.labels("matched").inc()

    logger.info(
        "match.created",
        extra={**log_context, "match_id": match_id},
    )

    return JoinResponse(queued=True, match_id=match_id)


@app.get("/match/{match_id}")
async def get_match(match_id: str, request: Request) -> dict:
    pool: ConnectionPool = request.app.state.pg
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, player_a, player_b, status, created_at FROM matches WHERE id = %s",
            (match_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="match not found")
    row["id"] = str(row["id"])
    row["created_at"] = row["created_at"].isoformat()
    return row


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
def ready(request: Request) -> JSONResponse:
    pool: ConnectionPool = request.app.state.pg
    rds: redis.Redis = request.app.state.redis
    checks: dict[str, str] = {}
    ok = True

    try:
        with pool.connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {e.__class__.__name__}"
        ok = False

    try:
        rds.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e.__class__.__name__}"
        ok = False

    return JSONResponse(status_code=200 if ok else 503, content=checks)
