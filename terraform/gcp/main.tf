provider "google" {
  zone    = var.zone
  region  = var.region
  project = "original-bot-481123-v7"
}

provider "kubernetes" {
  host  = "https://${google_container_cluster.default.endpoint}"
  token = data.google_client_config.provider.access_token
  cluster_ca_certificate = base64decode(
    google_container_cluster.default.master_auth[0].cluster_ca_certificate,
  )
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "gke-gcloud-auth-plugin"
  }
}

provider "helm" {
  kubernetes = {
    host  = "https://${google_container_cluster.default.endpoint}"
    token = data.google_client_config.provider.access_token
    cluster_ca_certificate = base64decode(
      google_container_cluster.default.master_auth[0].cluster_ca_certificate,
    )
    exec = {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "gke-gcloud-auth-plugin"
    }
  }
}

data "google_client_config" "provider" {}

resource "google_compute_network" "vpc_network" {
  name                    = "ml-server-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "vpc_subnet" {
  name          = "ml-server-subnet"
  ip_cidr_range = "10.0.0.0/20"
  network       = google_compute_network.vpc_network.id
  region        = var.region
}

resource "google_service_account" "default" {
  account_id   = "service-account-id"
  display_name = "Service Account"
}

resource "google_container_cluster" "default" {
  name                = "ml-server-cluster"
  location            = var.zone
  initial_node_count  = 2
  network             = google_compute_network.vpc_network.id
  subnetwork          = google_compute_subnetwork.vpc_subnet.id
  deletion_protection = false
  node_config {
    service_account = google_service_account.default.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    machine_type = "e2-standard-2"
  }
  gateway_api_config {
    channel = "CHANNEL_STANDARD"
  }
}

resource "google_compute_subnetwork" "proxy_subnet" {
  name          = "ml-server-proxy-subnet"
  ip_cidr_range = "10.0.16.0/24"
  network       = google_compute_network.vpc_network.id
  region        = var.region
  purpose       = "REGIONAL_MANAGED_PROXY"
  role          = "ACTIVE"
}

data "google_secret_manager_secret_version" "ml-server-github-argocd-token" {
  secret  = "ml-server-github-argocd-token"
  version = "latest"
}