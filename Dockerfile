FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY policies/ ./policies/

RUN pip install --upgrade pip && \
    pip install -e .

EXPOSE 8000

CMD ["uvicorn", "synpassport.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
