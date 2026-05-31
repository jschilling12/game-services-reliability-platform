import os

import pytest
from pydantic import ValidationError

os.environ.setdefault("POSTGRES_DSN", "postgresql://app:app@localhost:5432/matchmaking")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app import JoinRequest # noqa: E402


def test_join_request_accepts_valid_payload():
    req = JoinRequest(player_id="player-1", rank=100)
    assert req.player_id == "player-1"
    assert req.rank == 100


def test_join_request_rejects_empty_player_id():
    with pytest.raises(ValidationError):
        JoinRequest(player_id="", rank=100)