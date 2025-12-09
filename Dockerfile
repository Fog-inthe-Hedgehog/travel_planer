FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

# System dependencies for building psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry separately to leverage caching
RUN pip install --no-cache-dir poetry

# Copy dependency manifests first to leverage Docker cache
COPY pyproject.toml poetry.lock* ./

RUN poetry install --no-root

# Copy application source
COPY . .

CMD ["bash", "-c", "poetry run alembic upgrade head && poetry run python main.py"]
