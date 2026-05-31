import os
import sys

import redis

try:
    rds = redis.Redis.from_url(os.environ["REDIS_URL"], socket_timeout=2)
    rds.ping()
except Exception as e:
    print(f"redis unhealthy: {e}", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
