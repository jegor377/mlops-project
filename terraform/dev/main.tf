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

resource "null_resource" "gateway-api-crds" {
  depends_on = [kind_cluster.default]

  provisioner "local-exec" {
    command = "kubectl apply -f ${path.module}/../../k8s/crds/gateway-api-crds.yaml"
  }
}

resource "helm_release" "metallb" {
  depends_on = [null_resource.gateway-api-crds]
  name       = "metallb"
  repository = "https://metallb.github.io/metallb"
  chart      = "metallb"
  version    = "0.15.3"
  create_namespace = true
  namespace = "metallb-system"
}

resource "null_resource" "metallb_config" {
  depends_on = [helm_release.metallb]

  provisioner "local-exec" {
    command = "kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=metallb -n metallb-system --timeout=60s && kubectl apply -f ${path.module}/manifests/metallb-config.yaml"
  }
}

resource "helm_release" "traefik" {
  depends_on = [kind_cluster.default, null_resource.metallb_config]
  name       = "traefik"
  repository = "https://traefik.github.io/charts"
  chart      = "traefik"
  version    = "38.0.2"
  create_namespace = true
  namespace = "traefik-system"

  values = [
    file("${path.module}/traefik-values.yaml")
  ]
}

resource "null_resource" "traefik_config" {
  depends_on = [helm_release.traefik, null_resource.metallb_config]

  provisioner "local-exec" {
    command = "kubectl apply -f ${path.module}/manifests/GatewayClass.yaml"
  }
}