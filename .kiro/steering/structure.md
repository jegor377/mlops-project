# Project Structure

```
mlops-project/
├── devbox.d/                      # Devbox config files (Redis tools)
├── frontend/                      # React/TypeScript frontend
│   ├── app/                       # Main app code
│   │   ├── components/           # Reusable React components
│   │   ├── context/              # React contexts (auth, etc.)
│   │   ├── routes/               # Route components (React Router)
│   │   │   ├── contact-sales.tsx
│   │   │   ├── dashboard.tsx
│   │   │   ├── forgot-password.tsx
│   │   │   ├── home.tsx
│   │   │   ├── login.tsx
│   │   │   ├── register.tsx
│   │   │   └── reset-password.tsx
│   │   ├── app.css
│   │   ├── nav.tsx
│   │   ├── root.tsx              # Root route
│   │   ├── routes.ts             # Route definitions
│   │   └── withNav.tsx           # Nav wrapper HOC
│   ├── public/                   # Static assets
│   ├── .react-router/            # Generated types
│   └── Taskfile.yml              # Frontend tasks
├── k8s/                          # Kubernetes manifests
│   ├── argocd/                   # ArgoCD resources
│   │   └── apps/                 # ArgoCD Application manifests
│   └── services/                 # Service-specific K8s resources
│       ├── common-gw/            # Common gateway for frontend + ml_server
│       ├── frontend/             # Frontend service K8s manifests
│       └── ml_server/            # Backend service K8s manifests
│           ├── base/             # Base manifests
│           └── overlays/         # Environment overlays (dev/staging/production)
├── ml_server/                    # Python FastAPI backend
│   ├── src/ml_server/            # Main source code
│   │   ├── conf/                 # Pydantic-settings configuration
│   │   ├── dependencies/         # FastAPI dependencies
│   │   ├── enums/                # Enum definitions
│   │   ├── models/               # SQLAlchemy models
│   │   ├── routes/               # FastAPI route handlers
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── services/             # Business logic services
│   │   ├── utils/                # Utility functions
│   │   ├── app.py
│   │   ├── main.py
│   │   └── __init__.py
│   ├── tests/                    # Test code
│   │   ├── api/                  # Integration tests
│   │   └── unit/                 # Unit tests
│   ├── migrations/               # Alembic migrations
│   │   └── versions/
│   ├── init.sql                  # DB initialization script
│   ├── pyproject.toml            # Backend dependencies (FastAPI, SQLAlchemy, torch, etc.)
│   ├── uv.lock                   # Backend uv lock
│   └── Taskfile.yaml             # Backend tasks
├── terraform/                    # Terraform IaC
│   ├── dev/                      # Development environment manifests
│   └── gcp/                      # GCP production/staging resources
├── utils/                        # Utility Taskfiles (CI/CD versioning, etc.)
├── .devbox/                      # Devbox generated files
├── .venv/                        # Python virtual environment
├── .kiro/                        # Kiro configuration (steering, hooks, agents)
├── .vscode/                      # VS Code settings
├── .github/workflows/            # CI/CD pipelines
├── architecture.png              # Architecture diagram
├── dashboard.png                 # Dashboard screenshot
├── home_page.png                 # Home page screenshot
├── Taskfile.yaml                 # Root tasks
├── Tiltfile                      # Tilt configuration
├── devbox.json                   # Devbox package list
├── devbox.lock                   # Devbox locked versions
├── pyproject.toml                # Python tools (flake8, pre-commit, linting)
├── uv.lock                       # Root-level uv lock (for tools)
├── .env.example                  # Environment variables template
├── .gitignore
├── .pre-commit-config.yaml       # Pre-commit hooks
├── .flake8                       # Flake8 configuration
├── .isort.cfg                    # isort configuration
├── release-please-config.json    # Release automation config
├── .release-please-manifest.json
└── README.md                     # Project overview
```

## Key Patterns

- **Backend**: `src/ml_server/` contains all application code; `tests/` mirrors the structure
- **Frontend**: React Router file-based routing; `app/routes/` maps to URL paths
- **Kubernetes**: Kustomize overlays for environments (`dev`, `staging`, `production`)
- **Configuration**: Pydantic Settings for backend; environment variables for frontend

## Python Tooling Layout

- **Root `pyproject.toml`**: Python tools only (flake8, pre-commit). Run via `uv run flake8`, `uvx ruff format`
- **`ml_server/pyproject.toml`**: Actual backend dependencies (FastAPI, SQLAlchemy, torch, transformers, etc.)
- **Lock files**: Root `uv.lock` for tools; `ml_server/uv.lock` for app dependencies