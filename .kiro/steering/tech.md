# Tech Stack & Build System

## Languages & Runtimes
- **Python**: 3.12 (defined in `.python-version`)
- **Node.js**: Latest (via Devbox)
- **TypeScript**: Default for frontend

## Backend
- **Framework**: FastAPI
- **ORM**: SQLAlchemy (async)
- **Migrations**: Alembic
- **Schema**: Pydantic v2
- **Auth**: Authlib (OAuth2), bcrypt, HttpOnly sessions
- **ML**: HuggingFace Transformers (sentiment analysis)
- **Cache/Rate Limit**: Redis (sliding-window)
- **Database**: PostgreSQL (CNPG operator on GKE)

## Frontend
- **Framework**: React + TypeScript + React Router (Remix-style)
- **Styling**: Tailwind CSS
- **Build**: Vite (via React Router template)

## DevOps & Infrastructure
- **Container**: Docker, `uv` for Python dependency management
- **Orchestration**: Kubernetes (GKE), Kustomize
- **GitOps**: ArgoCD, Argo Rollouts (canary)
- **IaC**: Terraform
- **Ingress**: Traefik, GKE Gateway API
- **Testing**: pytest, pytest-asyncio (integration tests against real DB)

## Local Development Tools
- **Environment**: Devbox (Nix-based, portable dev environment)
- **Task Automation**: go-task (Taskfile)
- **K8s**: kind (local cluster), kubectl, kubectx, k9s, helm
- **Workflow Testing**: act (GitHub Actions local testing)
- **Email Testing**: Mailpit
- **GCP**: gcloud SDK (via Devbox)

## Common Commands

### Dependency Management
```bash
task sync-deps           # Sync all dependencies (repo + server)
task sync-repo-deps      # Sync repo-level dependencies
task sync-server-deps    # Sync ml_server dependencies
uv lock                  # Lock dependencies
```

### Backend
```bash
task ml_server:run-dev        # Run dev server with hot reload
task ml_server:upgrade-db     # Run Alembic migrations
task ml_server:new-migration  # Create new Alembic migration
task ml_server:test           # Run pytest (with real PostgreSQL/Redis containers. This can take even a few minutes to run. Always run from project root directory.)
task ml_server:test -- /path/to/the/file # Run pytest for a specific pytest file (with real PostgreSQL/Redis containers. This can take even a few minutes to run. Always run from project root directory.)
# example:
# task ml_server:test -- src/tests/api/test_register.py
```

### Frontend
```bash
cd frontend && npm run dev    # Start dev server (port 5173)
cd frontend && npm run build  # Build for production
```

### Docker
```bash
task build-images            # Build all Docker images
task push-images             # Push all images to registry
task ml_server:run-docker    # Run backend container locally
task frontend:run-docker     # Run frontend container locally
```

### Kubernetes
```bash
task k8s:port-forward        # Port-forward Traefik to port 80 (requires sudo)
```

### Code Quality
```bash
task lint                    # Run flake8 linter
uvx ruff format              # Run Black formatter
```

### Local Development Setup
```bash
task ml_server:create-docker-network
task ml_server:run-postgres
task ml_server:run-mailpit
task ml_server:run-redis
task ml_server:upgrade-db
task ml_server:run-dev
```