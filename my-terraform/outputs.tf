output "backend_url" {
  description = "The URL of the backend Cloud Run service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "The URL of the frontend Cloud Run service"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "cloud_sql_instance" {
  description = "The Cloud SQL connection name (used for Cloud Run socket)"
  value       = google_sql_database_instance.lumen_postgres.connection_name
}
