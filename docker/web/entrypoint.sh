#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

redis_ready() {
  python -c "
import sys
import os
import redis

try:
    r = redis.Redis(
        host=os.environ['REDIS_HOST'],
        port=os.environ['REDIS_PORT'],
        password=os.environ['REDIS_PASSWORD'],
        socket_connect_timeout=2,
    )
    r.ping()
    sys.exit(0)
except redis.exceptions.AuthenticationError as e:
    print(f'Redis authentication failed: {e}', file=sys.stderr)
    sys.exit(1)
except redis.exceptions.ConnectionError as e:
    print(f'Redis connection failed: {e}', file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f'An unexpected Redis error occurred: {e}', file=sys.stderr)
    sys.exit(1)
"
}

postgres_ready() {
  python -c "
import sys
import os
import psycopg2

try:
    conn = psycopg2.connect(
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        host=os.environ['DB_HOST'],
        port=os.environ['DB_PORT'],
        connect_timeout=3
    )
    conn.close()
    sys.exit(0)
except psycopg2.OperationalError as e:
    print(f'PostgreSQL connection failed: {e}', file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f'An unexpected PostgreSQL error occurred: {e}', file=sys.stderr)
    sys.exit(1)
"
}

until redis_ready; do
  >&2 echo 'Waiting for Redis to become available...'
  sleep 2
done
>&2 echo 'Redis is available.'

until postgres_ready; do
  >&2 echo 'Waiting for PostgreSQL to become available...'
  sleep 2
done
>&2 echo 'PostgreSQL is available.'

>&2 echo 'Applying database migrations...'
python manage.py migrate --noinput
>&2 echo 'Database migrations applied.'
>&2 echo 'Running collectstatic...'
python manage.py collectstatic --noinput
>&2 echo 'Collectstatic finished'

>&2 echo 'Starting webserver'
exec "$@"