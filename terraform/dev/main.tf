provider "kind" {
  # Configuration options
}

provider "helm" {
  kubernetes = {
    host                   = kind_cluster.default.endpoint
    cluster_ca_certificate = kind_cluster.default.cluster_ca_certificate
    client_certificate     = kind_cluster.default.client_certificate
    client_key             = kind_cluster.default.client_key
  }
}

provider "kubectl" {
  host                   = kind_cluster.default.endpoint
  cluster_ca_certificate = kind_cluster.default.cluster_ca_certificate
  client_certificate     = kind_cluster.default.client_certificate
  client_key             = kind_cluster.default.client_key
  load_config_file       = false # <-- important: ignore local kubeconfig entirely
}

resource "kind_cluster" "default" {
  name           = "dev-cluster"
  wait_for_ready = true
  node_image     = "kindest/node:v1.34.0"

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    node {
      role = "control-plane"
    }

    node {
      role = "worker"
    }

    node {
      role = "worker"
    }
  }
}

resource "kubectl_manifest" "gateway_api_crds" {
  depends_on = [kind_cluster.default]
  yaml_body  = file("${path.module}/manifests/gateway-api-crds.yaml")
}

resource "helm_release" "traefik" {
  depends_on       = [kind_cluster.default]
  name             = "traefik"
  repository       = "https://traefik.github.io/charts"
  chart            = "traefik"
  version          = "38.0.2"
  create_namespace = true
  namespace        = "traefik-system"
  wait             = false

  values = [
    file("${path.module}/traefik-values.yaml")
  ]
}

resource "kubectl_manifest" "traefik_config" {
  depends_on = [helm_release.traefik]
  yaml_body  = file("${path.module}/manifests/GatewayClass.yaml")
}

resource "helm_release" "cnpg" {
  depends_on       = [kind_cluster.default]
  name             = "cnpg"
  repository       = "https://cloudnative-pg.github.io/charts"
  chart            = "cloudnative-pg"
  version          = "0.28.0"
  create_namespace = true
  namespace        = "cloudnative-pg-system"
  # wait             = false
}

resource "helm_release" "redis" {
  depends_on = [ kind_cluster.default ]
  name = "bitnami"
  repository = "https://charts.bitnami.com/bitnami"
  chart = "redis"
  version = "27.0.10"
  create_namespace = true
  namespace = "redis-system"
}