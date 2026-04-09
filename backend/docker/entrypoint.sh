#!/bin/sh
set -e
python /app/docker/download_model.py
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
