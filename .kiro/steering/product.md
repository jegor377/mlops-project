# Product Overview

**Volta** is a ML inference API platform demonstrating end-to-end MLOps practices.

## Core Functionality

- **ML Inference**: HuggingFace sentiment analysis model served via REST API
- **Multi-tenant API**: Secure access with personal access tokens (PATs) and rate limiting
- **Authentication**: Server-side sessions with OAuth2 (Google/GitHub), email verification, and password reset flows
- **Dashboard**: React-based UI for token management and API interaction

## Target Users

Developers and data scientists who need to:
- Deploy ML models behind authenticated APIs
- Manage API access through tokens
- Monitor usage and interact with ML models via a web interface

## Deployment

Production-ready deployment on Google Kubernetes Engine (GKE) with:
- GitOps via ArgoCD
- Canary deployments via Argo Rollouts
- Full observability and audit logging
