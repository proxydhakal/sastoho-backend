#!/bin/sh
set -e

# Run migrations
alembic upgrade head

# Start Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
