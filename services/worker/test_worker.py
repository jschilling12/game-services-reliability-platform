import json
import os

os.environ.setdefault("POSTGRES_DSN", "postgresql://app:app@localhost:5432/matchmaking")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker import log_context, parse_match_payload # noqa: E402


def test_parse_match_payload_reads_correlation_fields():
    payload = {
        "match_id": "match-1",
        "request_id": "req-1",
        "match_request_id": "mr-1",
        "player_id": "player-1",
        "traceparent": "trace",
    }

    parsed = parse_match_payload(json.dumps(payload))

    assert parsed["match_id"] == "match-1"
    assert parsed["request_id"] == "req-1"
    assert parsed["match_request_id"] == "mr-1"
    assert parsed["player_id"] == "player-1"


def test_log_context_keeps_expected_fields():
    context = log_context({
        "match_id": "match-1",
        "request_id": "req-1",
        "match_request_id": "mr-1",
        "player_id": "player-1",
    })

    assert set(context) == {"match_id", "request_id", "match_request_id", "player_id"}