provider "kubectl" {
  host  = "https://${google_container_cluster.default.endpoint}"
  token = data.google_client_config.provider.access_token
  cluster_ca_certificate = base64decode(
    google_container_cluster.default.master_auth[0].cluster_ca_certificate,
  )
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "gke-gcloud-auth-plugin"
  }
  load_config_file = false # <-- important: ignore local kubeconfig entirely
}

resource "kubernetes_namespace" "argocd" {
  metadata {
    name = "argocd"
  }
}

data "http" "argocd_manifest" {
  url = "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"
}

data "kubectl_file_documents" "argocd" {
  content = data.http.argocd_manifest.response_body
}

resource "kubectl_manifest" "argocd" {
  for_each  = data.kubectl_file_documents.argocd.manifests
  yaml_body = each.value

  server_side_apply = true   # --server-side
  force_conflicts   = true   # --force-conflicts

  depends_on = [kubernetes_namespace.argocd]
}


resource "kubernetes_namespace" "argocd-rollouts" {
  metadata {
    name = "argocd-rollouts"
  }
}

data "http" "argocd-rollouts_manifest" {
  url = "https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml"
}

data "kubectl_file_documents" "argocd-rollouts" {
  content = data.http.argocd-rollouts_manifest.response_body
}

resource "kubectl_manifest" "argocd-rollouts" {
  for_each  = data.kubectl_file_documents.argocd-rollouts.manifests
  yaml_body = each.value

  depends_on = [kubectl_manifest.argocd, kubernetes_namespace.argocd-rollouts]
}

resource "kubectl_manifest" "ml-server-project" {
  depends_on = [kubectl_manifest.argocd, kubectl_manifest.argo-rollouts]
  yaml_body  = file("${path.module}/../../k8s/argocd/app-project-ml-server.yaml")
}

resource "kubectl_manifest" "platform-project" {
  depends_on = [kubectl_manifest.argocd, kubectl_manifest.argo-rollouts]
  yaml_body  = file("${path.module}/../../k8s/argocd/app-project-platform.yaml")
}

resource "kubectl_manifest" "root-app" {
  depends_on = [kubectl_manifest.ml-server-project, kubectl_manifest.platform-project]
  yaml_body  = file("${path.module}/../../k8s/argocd/root-app.yaml")
}

resource "kubernetes_secret_v1" "argocd_repo_secret" {
  depends_on = [kubectl_manifest.argocd]

  metadata {
    name      = "ml-server-repo"
    namespace = "argocd"
    labels = {
      "argocd.argoproj.io/secret-type" = "repository"
    }
  }

  data = {
    type     = "git"
    url      = "https://github.com/jegor377/mlops-project.git"
    password = local.github_pat
    username = "jegor377"
  }
}