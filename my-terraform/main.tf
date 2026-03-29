terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ────────────────────────────────────────
# Enable APIs
# ────────────────────────────────────────
resource "google_project_service" "cloud_run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secret_manager" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "compute" {
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "sqladmin" {
  service            = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifact_registry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}



# ────────────────────────────────────────
# Secrets — Conditionally Create
# ────────────────────────────────────────
resource "google_secret_manager_secret" "openai_key" {
  count     = var.create_secrets ? 1 : 0
  secret_id = "OPENAI_API_KEY"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret_version" "openai_key_value" {
  count       = var.create_secrets ? 1 : 0
  secret      = google_secret_manager_secret.openai_key[0].id
  secret_data = var.openai_api_key
}

resource "google_secret_manager_secret" "pinecone_key" {
  count     = var.create_secrets ? 1 : 0
  secret_id = "PINECONE_API_KEY"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret_version" "pinecone_key_value" {
  count       = var.create_secrets ? 1 : 0
  secret      = google_secret_manager_secret.pinecone_key[0].id
  secret_data = var.pinecone_api_key
}

resource "google_secret_manager_secret" "alpha_vantage_key" {
  count     = var.create_secrets ? 1 : 0
  secret_id = "ALPHA_VANTAGE_API_KEY"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret_version" "alpha_vantage_key_value" {
  count       = var.create_secrets ? 1 : 0
  secret      = google_secret_manager_secret.alpha_vantage_key[0].id
  secret_data = var.alpha_vantage_api_key
}

resource "google_secret_manager_secret" "database_url" {
  count     = var.create_secrets ? 1 : 0
  secret_id = "DATABASE_URL"
  replication { 
    auto {} 
    }
  depends_on = [google_project_service.secret_manager]
}

resource "google_secret_manager_secret_version" "database_url_value" {
  count       = var.create_secrets ? 1 : 0
  secret      = google_secret_manager_secret.database_url[0].id
  secret_data = "postgresql://postgres:${var.db_password}@/lumen?host=/cloudsql/${var.project_id}:${var.region}:lumen-postgres&sslmode=disable"
}


# ────────────────────────────────────────
# Locals — Handle both existing & new secrets
# ────────────────────────────────────────
locals {
  service_account = "${var.project_number}-compute@developer.gserviceaccount.com"

  openai_secret_id        = var.create_secrets ? google_secret_manager_secret.openai_key[0].id : "projects/${var.project_id}/secrets/OPENAI_API_KEY"
  pinecone_secret_id      = var.create_secrets ? google_secret_manager_secret.pinecone_key[0].id : "projects/${var.project_id}/secrets/PINECONE_API_KEY"
  alpha_vantage_secret_id = var.create_secrets ? google_secret_manager_secret.alpha_vantage_key[0].id : "projects/${var.project_id}/secrets/ALPHA_VANTAGE_API_KEY"
  database_url_secret_id  = var.create_secrets ? google_secret_manager_secret.database_url[0].id : "projects/${var.project_id}/secrets/DATABASE_URL"
}


# ────────────────────────────────────────
# Secret IAM — Grant Cloud Run access
# ────────────────────────────────────────
resource "google_secret_manager_secret_iam_member" "openai_access" {
  secret_id = local.openai_secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.service_account}"
}

resource "google_secret_manager_secret_iam_member" "pinecone_access" {
  secret_id = local.pinecone_secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.service_account}"
}

resource "google_secret_manager_secret_iam_member" "alpha_vantage_access" {
  secret_id = local.alpha_vantage_secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.service_account}"
}

resource "google_secret_manager_secret_iam_member" "database_url_access" {
  secret_id = local.database_url_secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.service_account}"
}


# ────────────────────────────────────────
# Cloud Run Service
# ────────────────────────────────────────
# Backend service with Cloud SQL connection and secrets
resource "google_cloud_run_v2_service" "backend" {
  name     = "lumen-backend"
  location = var.region

  template {
    annotations = {
      "run.googleapis.com/cloudsql-instances" = "${var.project_id}:${var.region}:lumen-postgres"
    }

    containers {
      image = var.backend_image
      command = ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port $${PORT:-8000}"]

      resources {
        limits = {
          memory = "2Gi"
          cpu    = "2"
        }
      }

      env {
        name  = "PINECONE_INDEX_NAME"
        value = "lumen-rag"
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = "DATABASE_URL"
            version = "latest"
          }
        }
      }

      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "OPENAI_API_KEY"
            version = "latest"
          }
        }
      }

      env {
        name = "PINECONE_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "PINECONE_API_KEY"
            version = "latest"
          }
        }
      }

      env {
        name = "ALPHA_VANTAGE_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "ALPHA_VANTAGE_API_KEY"
            version = "latest"
          }
        }
      }
    }
  }

  depends_on = [
    google_project_service.cloud_run,
    google_sql_database_instance.lumen_postgres,
    google_secret_manager_secret_iam_member.openai_access,
    google_secret_manager_secret_iam_member.pinecone_access,
    google_secret_manager_secret_iam_member.alpha_vantage_access,
    google_secret_manager_secret_iam_member.database_url_access,
  ]

}

# Frontend service (no secrets needed)
resource "google_cloud_run_v2_service" "frontend" {
  name     = "lumen-frontend"
  location = var.region

  template {
    containers {
      image = var.frontend_image
      command = ["sh", "-c", "python -m streamlit run app.py --server.port $${PORT:-8080} --server.address 0.0.0.0"]
      
      resources {
        limits = {
          memory = "1Gi"
          cpu    = "1"
        }
      }

      env {
        name  = "BACKEND_URL"
        value = google_cloud_run_v2_service.backend.uri
      }
    }
  }

  depends_on = [
    google_project_service.cloud_run,
    google_cloud_run_v2_service.backend,
  ]
}


# ────────────────────────────────────────
# Cloud SQL Service
# ────────────────────────────────────────

resource "google_sql_database_instance" "lumen_postgres" {
  name             = "lumen-postgres"
  database_version = "POSTGRES_16"
  region           = var.region
  deletion_protection = false

  settings {
    tier = var.db_tier
  }

  depends_on = [google_project_service.sqladmin]
}

resource "google_sql_database" "lumen_db" {
  name             = "lumen"
  instance         = google_sql_database_instance.lumen_postgres.name
  deletion_policy  = "ABANDON"
}

resource "google_sql_user" "lumen_user" {
  name            = "postgres"
  instance        = google_sql_database_instance.lumen_postgres.name
  password        = var.db_password
  deletion_policy = "ABANDON"
}

resource "google_project_iam_member" "cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${local.service_account}"
}


# ────────────────────────────────────────
# Artifact Registry
# ────────────────────────────────────────

resource "google_artifact_registry_repository" "lumen" {
  repository_id = "lumen"
  format        = "DOCKER"
  location      = var.region

  depends_on = [google_project_service.artifact_registry]
}


# ────────────────────────────────────────
# Allow unauthenticated access
# Frontend is public. Backend is invoked by the frontend service account only.
# ────────────────────────────────────────
resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  name     = google_cloud_run_v2_service.frontend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
