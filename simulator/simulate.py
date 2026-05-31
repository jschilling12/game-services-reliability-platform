#!/usr/bin/env python3
"""
Game backend load simulator.
Sends synthetic matchmaking, session, and telemetry traffic to the gateway.
"""

import argparse
import random
import time
import uuid
import urllib.request
import urllib.error
import json

DEFAULT_BASE_URL = "http://localhost:80"


def post(url: str, payload: dict) -> int:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except urllib.error.URLError:
        return 0


def simulate(base_url: str, rps: int, duration: int) -> None:
    print(f"Simulating {rps} req/s for {duration}s against {base_url}")
    interval = 1.0 / max(rps, 1)
    deadline = time.time() + duration
    total = ok = 0

    while time.time() < deadline:
        player_id = str(uuid.uuid4())

        # Queue a matchmaking request
        status = post(
            f"{base_url}/api/queue/join",
            {"player_id": player_id, "rank": random.randint(1, 100)},
        )
        total += 1
        if status in (200, 201, 202):
            ok += 1

        # Emit a telemetry event
        status = post(
            f"{base_url}/telemetry/ingest",
            {
                "player_id": player_id,
                "event": "match_requested",
                "ts": time.time(),
            },
        )
        total += 1
        if status in (200, 201, 202):
            ok += 1

        time.sleep(interval)

    print(f"Done: {ok}/{total} requests succeeded ({100*ok//max(total,1)}%)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Game backend simulator")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--rps", type=int, default=10, help="Requests per second")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds")
    args = parser.parse_args()
    simulate(args.base_url, args.rps, args.duration)


if __name__ == "__main__":
    main()
