FROM python:3.12.3-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

FROM base AS dev

COPY uv.lock pyproject.toml .

RUN uv sync

COPY src /app

EXPOSE 8000

CMD [ ".venv/bin/python", "-m", "uvicorn", "ml_server.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" ]

FROM base AS builder

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

FROM python:3.12.3-slim AS prod

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY src /app

EXPOSE 8000

CMD [ ".venv/bin/python", "-m", "uvicorn", "ml_server.main:app", "--host", "0.0.0.0", "--port", "8000" ]
