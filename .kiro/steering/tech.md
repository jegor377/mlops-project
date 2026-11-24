# Technology Stack

## Backend (ml_server)

- **Language**: Python 3.12
- **Framework**: FastAPI with async/await
- **ORM**: SQLAlchemy (async) with Alembic migrations
- **Database**: PostgreSQL (CloudNativePG operator on K8s)
- **Cache**: Redis (rate limiting, sessions)
- **Auth**: Authlib (OAuth2), bcrypt, HttpOnly cookies
- **ML**: HuggingFace Transformers (sentiment analysis)
- **Validation**: Pydantic v2
- **Testing**: pytest, pytest-asyncio (integration tests with real DB)

## Frontend

- **Language**: TypeScript
- **Framework**: React 19 with React Router 7 (formerly Remix)
- **Styling**: Tailwind CSS v4
- **Build**: Vite

## Infrastructure

- **Container**: Docker
- **Orchestration**: Kubernetes (GKE in production, kind for local)
- **Manifest Management**: Kustomize with overlays (dev/staging/production)
- **GitOps**: ArgoCD for continuous delivery
- **Progressive Delivery**: Argo Rollouts (canary strategy)
- **IaC**: Terraform for GCP resources
- **Ingress**: Traefik with Gateway API
- **Local Dev**: Tilt for hot-reload K8s development

## Development Tools

- **Package Manager**: `uv` for Python (fast, reproducible)
- **Task Runner**: Task (go-task) via Taskfile.yaml
- **Environment**: Devbox (isolated, reproducible dev shell)
- **CI/CD**: GitHub Actions
- **Release**: Release-Please automation
- **Local Testing**: act (run GH Actions locally), Mailpit (email)

## Code Quality

- **Formatter**: Black (line length: 88)
- **Import Sorting**: isort (black profile)
- **Linter**: flake8 (max-line-length: 88, ignore E203)
- **Pre-commit**: Configured with hooks for formatting, linting, K8s validation

## Common Commands

### Setup
```bash
# Install dependencies
task sync-deps              # All dependencies (repo + server)
task sync-repo-deps         # Root project only
task sync-server-deps       # ml_server only
task lock-deps              # Lock dependency versions

# Backend setup
cp ml_server/.env.example ml_server/.env
task ml_server:create-docker-network
task ml_server:run-postgres
task ml_server:run-redis
task ml_server:run-mailpit
task ml_server:upgrade-db   # Run Alembic migrations
```

### Development
```bash
# Start services
task ml_server:run-dev      # Backend (FastAPI with uvicorn)
task frontend:run-dev       # Frontend (Vite dev server)
task tilt-up                # Full K8s stack with hot-reload

# Code quality
task lint                   # Run flake8
task format                 # Run ruff format
pre-commit run --all-files  # Run all pre-commit hooks
```

### Testing
```bash
# Backend tests
cd ml_server
task ml_server:test                 # All tests
task ml_server:test -- tests/api    # Integration tests only
task ml_server:test -- tests/unit   # Unit tests only

# Frontend
cd frontend
npm run typecheck           # TypeScript + React Router typegen
```

### Docker
```bash
task build-images           # Build ml_server + frontend images
task push-images            # Push to registry
task ml_server:build-image  # Backend only
task frontend:build-image   # Frontend only
```

### Kubernetes (Local)
```bash
# Port-forward (requires sudo for port 80)
sudo env "PATH=$PATH" "KUBECONFIG=$HOME/.kube/config" task k8s:port-forward
```

## Architecture Patterns

- **Async-first**: All database and HTTP operations use async/await
- **Dependency Injection**: FastAPI dependencies for session, auth checks
- **Clean separation**: Routes → Services → Models pattern
- **Configuration**: pydantic-settings for type-safe env var loading
- **Secret Management**: `/run/secrets` for sensitive credentials
- **Testing**: Real infrastructure (PostgreSQL) in tests, not mocks
