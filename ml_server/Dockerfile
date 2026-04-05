FROM python:3.12.3-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN groupadd -g 1001 app && useradd -u 1001 -g app -m app

WORKDIR /app

# ──────────────────────────────────────────
# dev stage: used by Tilt for live reload
# ──────────────────────────────────────────
FROM base AS dev

COPY --chown=app:app uv.lock pyproject.toml ./

RUN uv sync

COPY --chown=app:app src ./

USER app

EXPOSE 8000

CMD [".venv/bin/python", "-m", "uvicorn", "ml_server.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ──────────────────────────────────────────
# builder stage: installs deps only (no project source)
# ──────────────────────────────────────────
FROM base AS builder

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# ──────────────────────────────────────────
# prod stage: lean final image
# ──────────────────────────────────────────
FROM python:3.12.3-slim AS prod

RUN groupadd -g 1001 app && useradd -u 1001 -g app -m app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app src ./

USER app

EXPOSE 8000

CMD [".venv/bin/python", "-m", "uvicorn", "ml_server.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]