# Builder Stage
FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY orchestrator/pyproject.toml orchestrator/uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    /bin/uv sync --frozen --no-install-project --no-dev

# Final Stage
FROM python:3.12-slim-bookworm
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

# Copy all needed app code
COPY app/ ./app/
COPY config/ ./config/
COPY models/ ./models/
COPY services/ ./services/
COPY pgvector/ ./pgvector/

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]