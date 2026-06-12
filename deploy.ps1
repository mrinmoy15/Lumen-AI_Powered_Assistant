# deploy.ps1
# Handles imports + terraform apply for Lumen

param(
    [string]$ProjectId,
    [string]$ProjectNumber,
    [string]$Region = "us-central1",
    [string]$ImageTag,
    [string]$AppName = "lumen"
)

# Normalize to lowercase — GCP resource names must be lowercase
$AppName = $AppName.ToLower()

$terraformDir = Join-Path $PSScriptRoot "my-terraform"

if (-not (Test-Path $terraformDir)) {
    Write-Host "[ERROR] Terraform directory not found at $terraformDir" -ForegroundColor Red
    exit 1
}

Set-Location $terraformDir
Write-Host "[DIR] Working directory: $terraformDir" -ForegroundColor Cyan

# ── Read secrets from environment variables ───────────────────────────────────
$openaiKey        = $env:OPENAI_API_KEY
$pineconeKey      = $env:PINECONE_API_KEY
$alphaVantageKey  = $env:ALPHA_VANTAGE_API_KEY
$dbPassword       = $env:POSTGRES_PASSWORD
$pineconeIndex    = $env:PINECONE_INDEX_NAME

if (-not $openaiKey)       { Write-Host "[ERROR] OPENAI_API_KEY env var is not set"        -ForegroundColor Red; exit 1 }
if (-not $pineconeKey)     { Write-Host "[ERROR] PINECONE_API_KEY env var is not set"      -ForegroundColor Red; exit 1 }
if (-not $alphaVantageKey) { Write-Host "[ERROR] ALPHA_VANTAGE_API_KEY env var is not set" -ForegroundColor Red; exit 1 }
if (-not $dbPassword)      { Write-Host "[ERROR] POSTGRES_PASSWORD env var is not set"     -ForegroundColor Red; exit 1 }
if (-not $pineconeIndex)   { Write-Host "[ERROR] PINECONE_INDEX_NAME env var is not set"   -ForegroundColor Red; exit 1 }

$fullImage = "$Region-docker.pkg.dev/$ProjectId/$AppName/$AppName`:$ImageTag"

$tfVars = @(
    "-var", "project_id=$ProjectId",
    "-var", "project_number=$ProjectNumber",
    "-var", "region=$Region",
    "-var", "app_name=$AppName",
    "-var", "backend_image=$fullImage",
    "-var", "frontend_image=$fullImage",
    "-var", "openai_api_key=$openaiKey",
    "-var", "pinecone_api_key=$pineconeKey",
    "-var", "pinecone_index_name=$pineconeIndex",
    "-var", "alpha_vantage_api_key=$alphaVantageKey",
    "-var", "db_password=$dbPassword"
)

# ── Step 0 — Set GCP Project ──────────────────────────────────────────────────
Write-Host ""
Write-Host "[GCP] Setting active project to $ProjectId..." -ForegroundColor Yellow
gcloud config set project $ProjectId
if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] Failed to set GCP project!" -ForegroundColor Red; exit 1 }
Write-Host "[OK] GCP project set to $ProjectId" -ForegroundColor Green

# ── Step 1 — Enable Artifact Registry API ────────────────────────────────────
Write-Host ""
Write-Host "[API] Enabling Artifact Registry API..." -ForegroundColor Yellow
gcloud services enable artifactregistry.googleapis.com --project=$ProjectId --quiet
Write-Host "[OK] Artifact Registry API ready" -ForegroundColor Green

# ── Step 2 — Terraform Init ───────────────────────────────────────────────────
Write-Host ""
Write-Host "[INIT] Initializing Terraform..." -ForegroundColor Yellow
terraform init
if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] Terraform init failed!" -ForegroundColor Red; exit 1 }
Write-Host "[OK] Terraform init successful!" -ForegroundColor Green

# ── Step 3 — Import Artifact Registry repo if it exists ──────────────────────
Write-Host ""
Write-Host "[CHECK] Checking if Artifact Registry repository '$AppName' exists..." -ForegroundColor Yellow
$repoExists = gcloud artifacts repositories list --location=$Region --filter="name~$AppName" --format="value(name)" --project=$ProjectId 2>$null
if ($repoExists) {
    Write-Host "[OK] Repository exists -- importing into Terraform state..." -ForegroundColor Green
    terraform import @tfVars google_artifact_registry_repository.lumen "projects/$ProjectId/locations/$Region/repositories/$AppName" 2>$null
} else {
    Write-Host "[NEW] Repository does not exist -- Terraform will create it" -ForegroundColor Blue
}

# ── Step 4 — Enable Cloud SQL API ────────────────────────────────────────────
Write-Host ""
Write-Host "[API] Enabling Cloud SQL API..." -ForegroundColor Yellow
gcloud services enable sqladmin.googleapis.com --project=$ProjectId --quiet
Write-Host "[OK] Cloud SQL API ready" -ForegroundColor Green

# ── Step 5 — Import Cloud SQL instance if it exists ──────────────────────────
Write-Host ""
Write-Host "[CHECK] Checking if Cloud SQL instance '$AppName-postgres' exists..." -ForegroundColor Yellow
$sqlExists = gcloud sql instances list --filter="name=$AppName-postgres" --format="value(name)" --project=$ProjectId 2>$null
if ($sqlExists) {
    Write-Host "[OK] Cloud SQL instance exists -- importing into Terraform state..." -ForegroundColor Green
    terraform import @tfVars google_sql_database_instance.lumen_postgres "projects/$ProjectId/instances/$AppName-postgres" 2>$null
} else {
    Write-Host "[NEW] Cloud SQL instance does not exist -- Terraform will create it" -ForegroundColor Blue
}

# ── Step 6 — Import Cloud Run services if they exist ─────────────────────────
Write-Host ""
Write-Host "[CHECK] Checking if Cloud Run backend service '$AppName-backend' exists..." -ForegroundColor Yellow
$backendExists = gcloud run services describe "$AppName-backend" --region=$Region --project=$ProjectId 2>$null
if ($backendExists) {
    Write-Host "[OK] Backend service exists -- importing into Terraform state..." -ForegroundColor Green
    terraform import @tfVars google_cloud_run_v2_service.backend "projects/$ProjectId/locations/$Region/services/$AppName-backend" 2>$null
} else {
    Write-Host "[NEW] Backend service does not exist -- Terraform will create it" -ForegroundColor Blue
}

Write-Host ""
Write-Host "[CHECK] Checking if Cloud Run frontend service '$AppName-frontend' exists..." -ForegroundColor Yellow
$frontendExists = gcloud run services describe "$AppName-frontend" --region=$Region --project=$ProjectId 2>$null
if ($frontendExists) {
    Write-Host "[OK] Frontend service exists -- importing into Terraform state..." -ForegroundColor Green
    terraform import @tfVars google_cloud_run_v2_service.frontend "projects/$ProjectId/locations/$Region/services/$AppName-frontend" 2>$null
} else {
    Write-Host "[NEW] Frontend service does not exist -- Terraform will create it" -ForegroundColor Blue
}

# ── Step 7 — Import Secrets if they exist ────────────────────────────────────
Write-Host ""
Write-Host "[CHECK] Checking if secrets exist in Terraform state..." -ForegroundColor Yellow
$secretInState = terraform state list 2>$null | Select-String "google_secret_manager_secret.openai_key"
if (-not $secretInState) {
    $secretExists = gcloud secrets describe OPENAI_API_KEY --project=$ProjectId 2>$null
    if ($secretExists) {
        Write-Host "[OK] Secrets exist outside Terraform -- importing into state..." -ForegroundColor Green
        terraform import @tfVars "google_secret_manager_secret.openai_key[0]"        "projects/$ProjectId/secrets/OPENAI_API_KEY"        2>$null
        terraform import @tfVars "google_secret_manager_secret.pinecone_key[0]"      "projects/$ProjectId/secrets/PINECONE_API_KEY"      2>$null
        terraform import @tfVars "google_secret_manager_secret.alpha_vantage_key[0]" "projects/$ProjectId/secrets/ALPHA_VANTAGE_API_KEY" 2>$null
        terraform import @tfVars "google_secret_manager_secret.database_url[0]"      "projects/$ProjectId/secrets/DATABASE_URL"          2>$null
        Write-Host "[OK] Secrets imported" -ForegroundColor Green
    } else {
        Write-Host "[NEW] Secrets do not exist -- Terraform will create them" -ForegroundColor Blue
    }
} else {
    Write-Host "[OK] Secrets already in Terraform state -- skipping import" -ForegroundColor Green
}

# ── Step 8 — Terraform Apply ──────────────────────────────────────────────────
Write-Host ""
Write-Host "[DEPLOY] Running terraform apply..." -ForegroundColor Yellow
terraform apply -auto-approve @tfVars

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Terraform apply failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Deployment Complete!                 " -ForegroundColor Green
Write-Host "   Frontend URL printed above           " -ForegroundColor Green
Write-Host "   as 'frontend_url' Terraform output   " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
exit 0
