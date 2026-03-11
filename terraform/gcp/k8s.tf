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

resource "helm_release" "argocd" {
  depends_on       = [google_container_cluster.default]
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  namespace        = "argocd"
  create_namespace = true
  version          = "9.4.10"
}

resource "helm_release" "argo_rollouts" {
  depends_on       = [helm_release.argocd]
  name             = "argo-rollouts"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-rollouts"
  namespace        = "argo-rollouts"
  create_namespace = true
  version          = "2.40.6"
}

resource "kubectl_manifest" "ml-server-project" {
  depends_on = [helm_release.argocd, helm_release.argo_rollouts]
  yaml_body  = file("${path.module}/../../k8s/argocd/app-project-ml-server.yaml")
}

resource "kubectl_manifest" "platform-project" {
  depends_on = [helm_release.argocd, helm_release.argo_rollouts]
  yaml_body  = file("${path.module}/../../k8s/argocd/app-project-platform.yaml")
}

resource "kubectl_manifest" "root-app" {
  depends_on = [kubectl_manifest.ml-server-project, kubectl_manifest.platform-project]
  yaml_body  = file("${path.module}/../../k8s/argocd/root-app.yaml")
}

resource "kubernetes_secret_v1" "argocd_repo_secret" {
  depends_on = [helm_release.argocd]

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