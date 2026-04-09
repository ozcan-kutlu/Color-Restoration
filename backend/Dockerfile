# API imajı: yalnızca `app` paketi (train/script imaja girmez).
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app/

RUN pip install --upgrade pip && pip install .

RUN mkdir -p /app/models

RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# PORT: Render ve benzeri platformlar çalışma zamanında atar; yoksa 8000 (ör. docker compose).
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD python -c "import os,urllib.request as u; p=os.environ.get('PORT','8000'); u.urlopen('http://127.0.0.1:'+p+'/api/v1/health', timeout=5)"

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
