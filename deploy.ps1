# deploy.ps1
# Full deploy: build backend + frontend images, push to Artifact Registry, apply Terraform.

param(
    [string]$ProjectId,
    [string]$ProjectNumber,
    [string]$Region = "us-central1",
    [string]$ImageTag,
    [string]$AppName = "lumen"
)

$AppName = $AppName.ToLower()

if (-not $ImageTag) {
    $ImageTag = "1.0.$(Get-Date -Format 'yyyyMMdd-HHmm')"
    Write-Host "[INFO] Auto-generated image tag: $ImageTag" -ForegroundColor Cyan
}

$RegistryHost    = "$Region-docker.pkg.dev"
$BackendImage    = "$RegistryHost/$ProjectId/$AppName/$AppName-backend`:$ImageTag"
$FrontendImage   = "$RegistryHost/$ProjectId/$AppName/$AppName-frontend`:$ImageTag"
$rootDir         = $PSScriptRoot
$terraformDir    = Join-Path $rootDir "my-terraform"
$tfvarsPath      = Join-Path $terraformDir "terraform.tfvars"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   LUMEN -- Deploy                      " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Backend : $BackendImage"
Write-Host "  Frontend: $FrontendImage"
Write-Host "  Region  : $Region"
Write-Host "  Project : $ProjectId"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $terraformDir)) { Write-Host "[ERROR] my-terraform/ not found" -ForegroundColor Red; exit 1 }
if (-not (Test-Path $tfvarsPath))   { Write-Host "[ERROR] terraform.tfvars not found" -ForegroundColor Red; exit 1 }

# -- Read secrets from environment -----------------------------------------------
$openaiKey       = $env:OPENAI_API_KEY
$pineconeKey     = $env:PINECONE_API_KEY
$alphaVantageKey = $env:ALPHA_VANTAGE_API_KEY
$dbPassword      = $env:POSTGRES_PASSWORD
$pineconeIndex   = $env:PINECONE_INDEX_NAME

if (-not $openaiKey)       { Write-Host "[ERROR] OPENAI_API_KEY is not set"        -ForegroundColor Red; exit 1 }
if (-not $pineconeKey)     { Write-Host "[ERROR] PINECONE_API_KEY is not set"      -ForegroundColor Red; exit 1 }
if (-not $alphaVantageKey) { Write-Host "[ERROR] ALPHA_VANTAGE_API_KEY is not set" -ForegroundColor Red; exit 1 }
if (-not $dbPassword)      { Write-Host "[ERROR] POSTGRES_PASSWORD is not set"     -ForegroundColor Red; exit 1 }
if (-not $pineconeIndex)   { Write-Host "[ERROR] PINECONE_INDEX_NAME is not set"   -ForegroundColor Red; exit 1 }

$tfVars = @(
    "-var", "project_id=$ProjectId",
    "-var", "project_number=$ProjectNumber",
    "-var", "region=$Region",
    "-var", "app_name=$AppName",
    "-var", "backend_image=$BackendImage",
    "-var", "frontend_image=$FrontendImage",
    "-var", "openai_api_key=$openaiKey",
    "-var", "pinecone_api_key=$pineconeKey",
    "-var", "pinecone_index_name=$pineconeIndex",
    "-var", "alpha_vantage_api_key=$alphaVantageKey",
    "-var", "db_password=$dbPassword"
)

# -- Step 1 - Set GCP project ----------------------------------------------------
Write-Host "[GCP] Setting active project to $ProjectId..." -ForegroundColor Yellow
gcloud config set project $ProjectId
if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] Failed to set GCP project" -ForegroundColor Red; exit 1 }
Write-Host "[OK] GCP project set" -ForegroundColor Green

# -- Step 2 - Enable Artifact Registry API ---------------------------------------
Write-Host ""
Write-Host "[API] Enabling Artifact Registry API..." -ForegroundColor Yellow
gcloud services enable artifactregistry.googleapis.com --project=$ProjectId --quiet
Write-Host "[OK] Artifact Registry API ready" -ForegroundColor Green

# -- Step 3 - Ensure Artifact Registry repo exists --------------------------------
Write-Host ""
Write-Host "[REGISTRY] Checking Artifact Registry repository '$AppName'..." -ForegroundColor Yellow
$repoExists = gcloud artifacts repositories describe $AppName --location=$Region --project=$ProjectId 2>$null
if ($repoExists) {
    Write-Host "[OK] Repository already exists" -ForegroundColor Green
} else {
    Write-Host "[NEW] Creating repository '$AppName'..." -ForegroundColor Blue
    gcloud artifacts repositories create $AppName `
        --repository-format=docker `
        --location=$Region `
        --project=$ProjectId
    if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] Failed to create repository" -ForegroundColor Red; exit 1 }
    Write-Host "[OK] Repository created" -ForegroundColor Green
}

# -- Step 4 - Docker auth --------------------------------------------------------
Write-Host ""
Write-Host "[AUTH] Configuring Docker for Artifact Registry..." -ForegroundColor Yellow
gcloud auth configure-docker $RegistryHost --quiet
if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] Docker auth failed" -ForegroundColor Red; exit 1 }
Write-Host "[OK] Docker authenticated" -ForegroundColor Green

# -- Step 5 - Build + push backend -----------------------------------------------
Write-Host ""
Write-Host "[BUILD] Building backend image: $BackendImage" -ForegroundColor Yellow
docker build -t $BackendImage (Join-Path $rootDir "backend")
if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] Backend build failed" -ForegroundColor Red; exit 1 }
Write-Host "[OK] Backend build successful" -ForegroundColor Green

Write-Host ""
Write-Host "[PUSH] Pushing backend image..." -ForegroundColor Yellow
docker push $BackendImage
if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] Backend push failed" -ForegroundColor Red; exit 1 }
Write-Host "[OK] Backend pushed" -ForegroundColor Green

# -- Step 6 - Build + push frontend ----------------------------------------------
Write-Host ""
Write-Host "[BUILD] Building frontend image: $FrontendImage" -ForegroundColor Yellow
docker build -t $FrontendImage (Join-Path $rootDir "frontend")
if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] Frontend build failed" -ForegroundColor Red; exit 1 }
Write-Host "[OK] Frontend build successful" -ForegroundColor Green

Write-Host ""
Write-Host "[PUSH] Pushing frontend image..." -ForegroundColor Yellow
docker push $FrontendImage
if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] Frontend push failed" -ForegroundColor Red; exit 1 }
Write-Host "[OK] Frontend pushed" -ForegroundColor Green

# -- Step 7 - Terraform init -----------------------------------------------------
Set-Location $terraformDir
Write-Host ""
Write-Host "[INIT] Initializing Terraform..." -ForegroundColor Yellow
terraform init
if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] Terraform init failed" -ForegroundColor Red; exit 1 }
Write-Host "[OK] Terraform init successful" -ForegroundColor Green

# -- Step 8 - Import Artifact Registry repo --------------------------------------
Write-Host ""
Write-Host "[IMPORT] Importing Artifact Registry repo into Terraform state..." -ForegroundColor Yellow
terraform import @tfVars google_artifact_registry_repository.lumen "projects/$ProjectId/locations/$Region/repositories/$AppName" 2>$null
Write-Host "[OK] Done (skipped if already in state)" -ForegroundColor Green

# -- Step 9 - Enable Cloud SQL API + import instance -----------------------------
Write-Host ""
Write-Host "[API] Enabling Cloud SQL API..." -ForegroundColor Yellow
gcloud services enable sqladmin.googleapis.com --project=$ProjectId --quiet
Write-Host "[OK] Cloud SQL API ready" -ForegroundColor Green

Write-Host ""
Write-Host "[CHECK] Checking if Cloud SQL instance '$AppName-postgres' exists..." -ForegroundColor Yellow
$sqlExists = gcloud sql instances list --filter="name=$AppName-postgres" --format="value(name)" --project=$ProjectId 2>$null
if ($sqlExists) {
    Write-Host "[OK] Instance exists -- importing into Terraform state..." -ForegroundColor Green
    terraform import @tfVars google_sql_database_instance.lumen_postgres "projects/$ProjectId/instances/$AppName-postgres" 2>$null
} else {
    Write-Host "[NEW] Instance does not exist -- Terraform will create it" -ForegroundColor Blue
}

# -- Step 10 - Import Cloud Run services -----------------------------------------
Write-Host ""
Write-Host "[CHECK] Checking Cloud Run services..." -ForegroundColor Yellow
$backendExists = gcloud run services describe "$AppName-backend" --region=$Region --project=$ProjectId 2>$null
if ($backendExists) {
    Write-Host "[OK] Backend exists -- importing..." -ForegroundColor Green
    terraform import @tfVars google_cloud_run_v2_service.backend "projects/$ProjectId/locations/$Region/services/$AppName-backend" 2>$null
} else {
    Write-Host "[NEW] Backend does not exist -- Terraform will create it" -ForegroundColor Blue
}

$frontendExists = gcloud run services describe "$AppName-frontend" --region=$Region --project=$ProjectId 2>$null
if ($frontendExists) {
    Write-Host "[OK] Frontend exists -- importing..." -ForegroundColor Green
    terraform import @tfVars google_cloud_run_v2_service.frontend "projects/$ProjectId/locations/$Region/services/$AppName-frontend" 2>$null
} else {
    Write-Host "[NEW] Frontend does not exist -- Terraform will create it" -ForegroundColor Blue
}

# -- Step 11 - Import Secrets ----------------------------------------------------
Write-Host ""
Write-Host "[CHECK] Checking secrets in Terraform state..." -ForegroundColor Yellow
$secretInState = terraform state list 2>$null | Select-String "google_secret_manager_secret.openai_key"
if (-not $secretInState) {
    $secretExists = gcloud secrets describe OPENAI_API_KEY --project=$ProjectId 2>$null
    if ($secretExists) {
        Write-Host "[OK] Secrets exist -- importing into state..." -ForegroundColor Green
        terraform import @tfVars "google_secret_manager_secret.openai_key[0]"        "projects/$ProjectId/secrets/OPENAI_API_KEY"        2>$null
        terraform import @tfVars "google_secret_manager_secret.pinecone_key[0]"      "projects/$ProjectId/secrets/PINECONE_API_KEY"      2>$null
        terraform import @tfVars "google_secret_manager_secret.alpha_vantage_key[0]" "projects/$ProjectId/secrets/ALPHA_VANTAGE_API_KEY" 2>$null
        terraform import @tfVars "google_secret_manager_secret.database_url[0]"      "projects/$ProjectId/secrets/DATABASE_URL"          2>$null
        Write-Host "[OK] Secrets imported" -ForegroundColor Green
    } else {
        Write-Host "[NEW] Secrets do not exist -- Terraform will create them" -ForegroundColor Blue
    }
} else {
    Write-Host "[OK] Secrets already in Terraform state -- skipping" -ForegroundColor Green
}

# -- Step 12 - Terraform apply ---------------------------------------------------
Write-Host ""
Write-Host "[DEPLOY] Running terraform apply..." -ForegroundColor Yellow
terraform apply -auto-approve @tfVars
if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] Terraform apply failed" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Deploy Complete!                     " -ForegroundColor Green
Write-Host "   Frontend URL shown above             " -ForegroundColor Green
Write-Host "   as 'frontend_url' Terraform output   " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
