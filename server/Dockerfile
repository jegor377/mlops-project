# Install uv
FROM python:3.12.3-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

# Copy the project into the intermediate image
COPY . /app

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

FROM python:3.12.3-slim AS runner

WORKDIR /app

# create writable cache dirs
RUN mkdir -p /app/.cache && chown -R 1001:1001 /app

# Copy the environment, but not the source code
COPY --from=builder --chown=1001:1001 /app/.venv /app/.venv
COPY --chown=1001:1001 ./src /app

USER 1001

EXPOSE 8000

CMD [ "/app/.venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" ]
