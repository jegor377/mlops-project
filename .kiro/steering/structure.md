# Project Structure

## Root Layout

```
mlops-project/
├── ml_server/          # Backend Python service
├── frontend/           # React TypeScript frontend
├── k8s/                # Kubernetes manifests and ArgoCD apps
├── terraform/          # Infrastructure as Code (GCP, GKE)
├── models/             # ML model weights (PyTorch)
├── utils/              # CI/CD helper tasks
├── devbox.d/           # Devbox config files (e.g., Redis)
├── gcloud/             # GCP tools for Devbox
├── .github/workflows/  # CI/CD pipelines
├── Taskfile.yaml       # Root task definitions
├── Tiltfile            # Local K8s development orchestration
├── pyproject.toml      # Root Python project (pre-commit, flake8)
└── devbox.json         # Dev environment specification
```

## Backend (ml_server/)

```
ml_server/
├── src/ml_server/
│   ├── app.py              # FastAPI app factory
│   ├── main.py             # Entry point (uvicorn)
│   ├── conf/               # pydantic-settings configuration
│   ├── dependencies/       # FastAPI dependency injection
│   ├── models/             # SQLAlchemy ORM models
│   ├── routes/             # FastAPI route handlers (by domain)
│   ├── schemas/            # Pydantic request/response schemas
│   ├── services/           # Business logic (email, ML inference, etc.)
│   └── utils/              # Helper functions
├── migrations/             # Alembic database migrations
│   └── versions/
├── tests/
│   ├── api/                # Integration tests (real DB)
│   └── unit/               # Unit tests
├── pyproject.toml          # Dependencies, pytest config
├── Dockerfile
└── Taskfile.yaml
```

### Backend Patterns

- **Routes** define HTTP endpoints and use dependencies for auth, DB sessions
- **Services** contain business logic (e.g., `AuthService`, `MLService`)
- **Models** are SQLAlchemy tables (`User`, `PAT`, `AuditLog`)
- **Schemas** validate requests/responses via Pydantic
- **Dependencies** inject `AsyncSession`, `User`, rate limit checks
- **Config** loaded from environment via `pydantic-settings` classes

## Frontend (frontend/)

```
frontend/
├── app/
│   ├── routes/             # React Router pages (home, login, dashboard, etc.)
│   ├── components/         # Reusable React components
│   ├── context/            # React contexts (AuthContext)
│   ├── root.tsx            # Root layout
│   └── withNav.tsx         # Layout with navigation bar
├── public/                 # Static assets (favicon, images)
├── package.json
├── Dockerfile
├── Taskfile.yml
└── tsconfig.json
```

### Frontend Patterns

- **routes/**: Each file is a React Router route (e.g., `login.tsx` → `/login`)
- **context/**: `AuthContext` provides user session and `refetch()` helper
- **components/**: Shared UI components (buttons, forms, etc.)
- **Layouts**: `root.tsx` wraps all routes; `withNav.tsx` adds navigation bar

## Kubernetes (k8s/)

```
k8s/
├── argocd/
│   └── apps/               # ArgoCD Application manifests
│       ├── ml-server-app.yaml
│       ├── frontend-app.yaml
│       └── cnpg-cluster-app.yaml
└── services/
    ├── ml_server/
    │   ├── base/           # Base K8s manifests
    │   └── overlays/       # Environment-specific (dev/staging/production)
    │       ├── common/
    │       ├── dev/
    │       │   ├── manifests/
    │       │   └── patches/
    │       ├── staging/
    │       │   └── patches/
    │       └── production/
    │           └── patches/
    ├── frontend/           # Same structure as ml_server
    │   ├── base/
    │   └── overlays/
    └── common-gw/          # Gateway API HTTPRoute (shared ingress)
        ├── base/
        └── overlays/
```

### Kubernetes Patterns

- **Kustomize** manages environment overlays (dev/staging/production)
- **dev** overlay: Converts Argo Rollout → plain Deployment (no canary)
- **staging/production**: Use Argo Rollout with canary strategy
- **PreSync hooks**: Run Alembic migrations before deployment
- **CNPG**: PostgreSQL operator manages DB lifecycle

## Terraform (terraform/)

```
terraform/
├── dev/
│   └── manifests/          # K8s helper resources (Gateway API CRDs)
└── gcp/                    # GKE cluster, VPC, IAM, MetalLB, Traefik
```

## Configuration Files

- **Taskfile.yaml**: Task runner definitions (includes per-service taskfiles)
- **Tiltfile**: Tilt orchestration for local K8s hot-reload
- **devbox.json**: Dev environment packages (kubectl, helm, k9s, etc.)
- **pyproject.toml**: Python dependencies and pytest config
- **.pre-commit-config.yaml**: Pre-commit hooks (black, isort, flake8, kluctl)
- **.flake8**, **.isort.cfg**: Code style configuration
- **.env.example**, **ml_server/.env.example**: Environment variable templates

## Naming Conventions

- **Python**: snake_case for functions/variables, PascalCase for classes
- **TypeScript**: camelCase for functions/variables, PascalCase for components
- **Files**: kebab-case for frontend routes, snake_case for Python modules
- **K8s resources**: kebab-case (e.g., `ml-server-deployment`)
- **Docker images**: snake_case in repo vars (`ml_server`, `frontend`)

## Key Directories to Know

- `ml_server/src/ml_server/routes/`: Add new API endpoints here
- `ml_server/migrations/versions/`: Alembic database migrations
- `frontend/app/routes/`: Add new pages here
- `k8s/services/*/overlays/`: Environment-specific K8s config
- `.github/workflows/`: CI/CD pipeline definitions
