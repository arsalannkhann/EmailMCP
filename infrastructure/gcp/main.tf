# EmailMCP GCP Infrastructure with Terraform

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "service_name" {
  description = "Service name"
  type        = string
  default     = "emailmcp"
}

# Provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secretmanager" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "firestore" {
  service            = "firestore.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifactregistry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudbuild" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

# Service Account
resource "google_service_account" "emailmcp" {
  account_id   = "${var.service_name}-service"
  display_name = "EmailMCP Service Account"
  description  = "Service account for EmailMCP Cloud Run service"
}

# Grant Secret Manager access
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.emailmcp.email}"
}

# Grant Firestore access
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.emailmcp.email}"
}

# Artifact Registry Repository
resource "google_artifact_registry_repository" "emailmcp" {
  location      = var.region
  repository_id = var.service_name
  description   = "EmailMCP Docker repository"
  format        = "DOCKER"
}

# Secret for Gmail OAuth Configuration
resource "google_secret_manager_secret" "gmail_oauth" {
  secret_id = "${var.service_name}-gmail-oauth-config"
  
  replication {
    auto {}
  }
  
  labels = {
    service     = var.service_name
    environment = var.environment
  }
}

# Secret for API Key
resource "google_secret_manager_secret" "api_key" {
  secret_id = "${var.service_name}-api-key"
  
  replication {
    auto {}
  }
  
  labels = {
    service     = var.service_name
    environment = var.environment
  }
}

# Cloud Run Service
resource "google_cloud_run_service" "emailmcp" {
  name     = var.service_name
  location = var.region
  
  template {
    spec {
      service_account_name = google_service_account.emailmcp.email
      
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.service_name}/${var.service_name}:latest"
        
        ports {
          container_port = 8080
        }
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "1Gi"
          }
        }
        
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }
        
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "GCP_REGION"
          value = var.region
        }
        
        env {
          name  = "PREFERRED_EMAIL_PROVIDER"
          value = "gmail_api"
        }
        
        env {
          name  = "LOG_LEVEL"
          value = "INFO"
        }
        
        env {
          name = "MCP_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.api_key.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "GMAIL_CLIENT_ID"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.gmail_oauth.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "GMAIL_CLIENT_SECRET"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.gmail_oauth.secret_id
              key  = "latest"
            }
          }
        }
      }
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"
        "autoscaling.knative.dev/maxScale" = "10"
        "run.googleapis.com/client-name"   = "terraform"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [
    google_project_service.run,
    google_service_account.emailmcp
  ]
}

# Allow unauthenticated access to Cloud Run service
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.emailmcp.name
  location = google_cloud_run_service.emailmcp.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_service.emailmcp.status[0].url
}

output "service_account_email" {
  description = "Email of the service account"
  value       = google_service_account.emailmcp.email
}

output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.service_name}"
}

output "secrets" {
  description = "Secret Manager secret IDs"
  value = {
    gmail_oauth = google_secret_manager_secret.gmail_oauth.secret_id
    api_key     = google_secret_manager_secret.api_key.secret_id
  }
}
