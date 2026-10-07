FROM python:3.12-slim AS builder-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.10.7 /uv /uvx /bin/
COPY pyproject.toml uv.lock* ./

RUN uv sync --frozen --no-dev --no-install-project


FROM builder-base AS test
RUN uv sync --frozen
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY tests/ ./tests/
COPY alembic.ini pyproject.toml ./
ENV PYTHONPATH="/app" \
    PATH="/app/.venv/bin:$PATH"
CMD ["pytest", "-v"]


FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 1000 appuser \
    && useradd -u 1000 -g appuser -s /bin/sh appuser \
    && mkdir -p /app /logs \
    && chown -R appuser:appuser /app /logs

COPY --from=builder-base --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini pyproject.toml ./

USER appuser

EXPOSE 8001

CMD ["sh", "-c", "alembic upgrade head && python -m src.seed && uvicorn src.main:app --host 0.0.0.0 --port 8001"]
