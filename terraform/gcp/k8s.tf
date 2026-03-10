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

resource "kubernetes_namespace_v1" "argocd" {
  metadata {
    name = "argocd"
  }
}

resource "kubernetes_namespace_v1" "argo-rollouts" {
  metadata {
    name = "argo-rollouts"
  }
}

resource "null_resource" "argocd" {
  depends_on = [ kubernetes_namespace_v1.argocd ]

  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = "kubectl apply -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.3.3/manifests/install.yaml"
  }

  provisioner "local-exec" {
    when    = destroy
    command = "kubectl delete -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.3.3/manifests/install.yaml"
  }
}

resource "null_resource" "argo-rollouts" {
  depends_on = [ null_resource.argocd, kubernetes_namespace_v1.argo-rollouts ]

  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = "kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/download/v1.8.4/install.yaml"
  }

  provisioner "local-exec" {
    when    = destroy
    command = "kubectl delete -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/download/v1.8.4/install.yaml"
  }
}

resource "kubectl_manifest" "ml-server-project" {
  depends_on = [null_resource.argocd, null_resource.argo-rollouts]
  yaml_body  = file("${path.module}/../../k8s/argocd/app-project-ml-server.yaml")
}

resource "kubectl_manifest" "platform-project" {
  depends_on = [null_resource.argocd, null_resource.argo-rollouts]
  yaml_body  = file("${path.module}/../../k8s/argocd/app-project-platform.yaml")
}

resource "kubectl_manifest" "root-app" {
  depends_on = [kubectl_manifest.ml-server-project, kubectl_manifest.platform-project]
  yaml_body  = file("${path.module}/../../k8s/argocd/root-app.yaml")
}

resource "kubernetes_secret_v1" "argocd_repo_secret" {
  depends_on = [null_resource.argocd]

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