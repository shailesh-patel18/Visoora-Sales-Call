# =====================================================================
# GCP GKE MULTI-TENANT HIGH-CONCURRENCY INFRASTRUCTURE PROVISIONING
# =====================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.10.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ----------------------------------------------------
# 1. VPC network & Subnets
# ----------------------------------------------------
resource "google_compute_network" "vpc" {
  name                    = "visoora-prod-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "visoora-prod-subnet"
  ip_cidr_range = "10.0.0.0/20"
  region        = var.region
  network       = google_compute_network.vpc.id

  # Enables GKE private clusters communication
  private_ip_google_access = true
}

# ----------------------------------------------------
# 2. GKE Standard Control Plane
# ----------------------------------------------------
resource "google_container_cluster" "gke_cluster" {
  name     = "visoora-prod-gke-cluster"
  location = var.zone

  network    = google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.subnet.id

  # Deletes default node pool immediately to deploy isolated customized pools
  remove_default_node_pool = true
  initial_node_count       = 1

  ip_allocation_policy {
    cluster_ipv4_cidr_block  = "/14"
    services_ipv4_cidr_block = "/20"
  }
}

# ----------------------------------------------------
# 3. GKE Node Pool A: General Purpose Services
# ----------------------------------------------------
resource "google_container_node_pool" "general_pool" {
  name       = "general-pool"
  location   = var.zone
  cluster    = google_container_cluster.gke_cluster.name
  node_count = 3

  node_config {
    preemptible  = false
    machine_type = "e2-standard-4" # 4 vCPUs, 16 GB Memory

    labels = {
      role = "general"
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

# ----------------------------------------------------
# 4. GKE Node Pool B: Audio Optimized Compute Nodes
# ----------------------------------------------------
resource "google_container_node_pool" "audio_pool" {
  name       = "audio-optimized-pool"
  location   = var.zone
  cluster    = google_container_cluster.gke_cluster.name
  node_count = 2

  node_config {
    preemptible  = false
    # Compute-optimized high-frequency CPUs (guarantees VAD processing speed without jitter)
    machine_type = "c2-standard-4" # 4 vCPUs, 16 GB Memory

    labels = {
      role = "audio-processor"
    }

    # Pin pods to this node pool strictly using taints/tolerations or nodeSelector
    metadata = {
      disable-legacy-endpoints = "true"
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

# ----------------------------------------------------
# 5. Cloud Memorystore Redis (State & Session Affinity Store)
# ----------------------------------------------------
resource "google_redis_instance" "redis_cache" {
  name           = "visoora-prod-redis"
  tier           = "STANDARD_HA" # Highly Available Multi-AZ Failover setup
  memory_size_gb = 5

  location_id      = var.zone
  alternative_location_id = var.alt_zone

  authorized_network = google_compute_network.vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  redis_version = "REDIS_7_0"
  display_name  = "Visoora Telephony Redis"
}

# ----------------------------------------------------
# 6. Cloud SQL Postgres (Multi-Tenant Compliance DB)
# ----------------------------------------------------
resource "google_sql_database_instance" "postgres_db" {
  name             = "visoora-prod-postgres"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-custom-4-16384" # 4 vCPUs, 16 GB RAM

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }

    backup_configuration {
      enabled            = true
      point_in_time_recovery_enabled = true
    }
  }
}

# ----------------------------------------------------
# 7. Secret Manager (Encrypted Credentials)
# ----------------------------------------------------
resource "google_secret_manager_secret" "twilio_token" {
  secret_id = "twilio-auth-token"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "supabase_key" {
  secret_id = "supabase-service-role-key"
  replication {
    auto {}
  }
}

# ----------------------------------------------------
# Variables Declarations
# ----------------------------------------------------
variable "project_id" {
  type        = string
  description = "GCP Project Identifier"
  default     = "visoora-prod-gcp"
}

variable "region" {
  type        = string
  description = "Primary Deployment Region"
  default     = "us-central1"
}

variable "zone" {
  type        = string
  description = "Primary Compute Zone"
  default     = "us-central1-a"
}

variable "alt_zone" {
  type        = string
  description = "Alternative AZ Zone"
  default     = "us-central1-b"
}
