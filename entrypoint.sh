#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
python << 'EOF'
import socket
import time
import os

host = os.getenv('DB_HOST', 'db')
port = int(os.getenv('DB_PORT', '5432'))

for i in range(30):
    try:
        sock = socket.create_connection((host, port), timeout=2)
        sock.close()
        print(f"PostgreSQL is ready at {host}:{port}")
        break
    except (socket.error, ConnectionRefusedError):
        print(f"Waiting for PostgreSQL ({i+1}/30)...")
        time.sleep(1)
else:
    print("Could not connect to PostgreSQL")
    exit(1)
EOF

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 2 \
    --worker-class gthread \
    --access-logfile - \
    --error-logfile -
