# Product: Volta — ML Inference API Platform

Volta is a production-grade MLOps platform that exposes a HuggingFace sentiment analysis model through a secure, multi-tenant REST API. It demonstrates real-world MLOps and Platform Engineering practices including:

- **Authentication & Authorization**: Server-side sessions (HttpOnly cookies), Personal Access Tokens (PAT), OAuth2 social login (Google/GitHub), email verification, password reset flow
- **API Infrastructure**: Redis-backed rate limiting, structured error responses, audit logging
- **ML Serving**: FastAPI backend serving HuggingFace transformers model
- **Frontend**: React/TypeScript dashboard with React Router
- **Infrastructure**: Kubernetes (GKE), ArgoCD GitOps, Argo Rollouts canary deployments, Terraform IaC

## Target Deployment
Google Kubernetes Engine (GKE) with GitOps workflow driven by ArgoCD.

## Key Workflows
- Development: `devbox` for environment, `Task` for automation, `tilt` for local K8s dev
- Testing: pytest against real PostgreSQL/Redis containers (Redis mocked, DB not)
- CI/CD: GitHub Actions → Docker build → ArgoCD sync
- Release: Release-Please automation