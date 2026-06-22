#!/bin/sh
set -e

python - <<'PY'
import os
import socket
import time
from sqlalchemy.engine import make_url

url = make_url(os.environ["DATABASE_URL"])
host = url.host
port = url.port or 3306

for attempt in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"MySQL is ready at {host}:{port}")
            break
    except OSError:
        print(f"Waiting for MySQL at {host}:{port}...")
        time.sleep(2)
else:
    raise SystemExit("MySQL did not become ready")
PY

if [ -f alembic.ini ]; then
  alembic upgrade head
fi

python -m app.init_db

exec uvicorn app.main:app --host 0.0.0.0 --port 3000
