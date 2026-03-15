#!/bin/bash
set -e

echo "Attempting database migrations..."
alembic upgrade head || echo "WARNING: Migrations failed (database may not be ready yet). Continuing..."

echo "Starting server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
