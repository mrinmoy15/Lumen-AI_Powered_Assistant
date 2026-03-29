# Terraform variables for Lumen AI-Powered Assistant 
# deployment on GCP
#=========================================================
# GCP Project and region configuration
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "project_number" {
  description = "GCP Project Number"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

#========================================================
# API Keys
variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

variable "pinecone_api_key" {
  description = "Pinecone API Key"
  type        = string
  sensitive   = true
}

variable "alpha_vantage_api_key" {
  description = "Alpha Vantage API Key"
  type        = string
  sensitive   = true
}

#========================================================
# Cloud SQL (new — Postgres)
variable "db_password" {
  description = "PostgreSQL database password"
  type        = string
  sensitive   = true
}

variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
}

#========================================================
# Images and services
variable "backend_image" {
  description = "Full Artifact Registry path for the backend image"
  type        = string
}

variable "frontend_image" {
  description = "Full Artifact Registry path for the frontend image"
  type        = string
}

#========================================================
# Other configuration
variable "create_secrets" {
  description = "Set to false if secrets already exist in GCP Secret Manager"
  type        = bool
  default     = true
}

