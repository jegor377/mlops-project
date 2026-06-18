# Infrastructure

This document covers how to set up the Volta infrastructure locally (kind) and on GCP/GKE.

---

## Prerequisites

Install all tools via devbox:

```bash
devbox install
```

Or manually ensure you have:

- Docker
- `kind`
- `kubectl`
- `helm`
- `terraform`
- `argocd` CLI
- `go-task`
- `uv` (Python deps)

---

## Local Development (kind)

The local stack runs on a `kind` cluster with Traefik as the Gateway API controller. ArgoCD runs only for production and staging. Locally the rollout resources are transformed into deployments. PostgreSQL is managed via CNPG, Redis via Bitnami Helm chart.

### 1. Spin up the cluster and infrastructure

```bash
task terraform:dev:apply
```

This provisions the kind cluster and installs core infrastructure components (Traefik, CNPG operator, Redis).

### 2. Apply Kubernetes resources

```bash
task k8s:apply-dev-resources
```

### 3. Create required secrets

The backend requires several secrets. Create them manually if you're not using a cloud secret store:

```bash
# Google OAuth2
kubectl create secret generic google-oauth2-creds-client-secret \
  --from-literal=data=<your-google-oauth2-client-secret> \
  -n ml-server-dev

# GitHub OAuth2
kubectl create secret generic github-oauth2-creds-client-secret \
  --from-literal=data=<your-github-oauth2-client-secret> \
  -n ml-server-dev

# Starlette SessionMiddleware secret key (any random string)
kubectl create secret generic oauth-state-session-secret-key \
  --from-literal=data=<your-session-secret-key> \
  -n ml-server-dev

# Copy Redis credentials into ml-server-dev namespace
kubectl get secret bitnami-redis -n redis-system -o yaml \
  | sed 's/namespace: redis-system/namespace: ml-server-dev/' \
  | kubectl apply -n ml-server-dev -f -
```

> **Note:** The session secret key can be any random string — it's used by Starlette's `SessionMiddleware` to sign session cookies.

### 4. Port-forward all services

```bash
task k8s:port-forward
```

---

## GCP / GKE (Staging & Production)

The GCP environment is managed by Terraform under `terraform/gcp/`. It provisions:

- GKE cluster (Autopilot or Standard)
- VPC and subnets
- GCP IAM service accounts
- MetalLB, Traefik (Gateway API controller)
- CNPG PostgreSQL operator
- ArgoCD

### 1. Authenticate to GCP

```bash
gcloud auth application-default login
```

### 2. Apply Terraform

```bash
task terraform:gcp:apply
```

### 3. Configure kubectl

```bash
gcloud container clusters get-credentials <cluster-name> --region <region>
```

### 4. Bootstrap ArgoCD

ArgoCD applications are defined under `k8s/argocd/apps/`. Once ArgoCD is running, apply the app manifests:

```bash
task k8s:apply-root-app
```

ArgoCD will pick up the Kustomize overlays for `staging` and `production` and manage all deployments from that point. Alembic migrations run automatically as ArgoCD PreSync hook Jobs before each rollout.

---

## Overlay Strategy

| Environment | Deployment type | Notes |
|---|---|---|
| `dev` | Plain `Deployment` | Argo Rollout converted via JSON patch |
| `staging` | `Rollout` (canary) | 33% → manual approval → 66% → 100% after 10s |
| `production` | `Rollout` (canary) | Same strategy, production namespace |

---

## Continuous Delivery

After initial bootstrap, all deploys are driven by GitHub Actions:

1. CI passes (lint → test → Docker build)
2. Action updates the image tag in the Kustomize overlay
3. ArgoCD detects the change and syncs
4. PreSync hook runs Alembic migrations
5. Argo Rollouts executes the canary strategy

No manual `kubectl apply` is needed for day-to-day deployments.