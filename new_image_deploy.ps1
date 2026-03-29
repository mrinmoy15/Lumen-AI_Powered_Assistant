# ────────────────────────────────────────
# new_image_deploy.ps1
# Full automated build + push + deploy for Lumen
# Uses Artifact Registry instead of Docker Hub
# ────────────────────────────────────────

param(
    [string]$ProjectId,
    [string]$ProjectNumber,
    [string]$Region = "us-central1",
    [string]$ImageTag
)

# ────────────────────────────────────────
# Auto-generate image tag if not provided
# ────────────────────────────────────────
if (-not $ImageTag) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmm"
    $ImageTag = "1.0.$timestamp"
    Write-Host "[INFO] Auto-generated image tag: $ImageTag" -ForegroundColor Cyan
}

$RegistryHost  = "$Region-docker.pkg.dev"
$FullImageName = "$RegistryHost/$ProjectId/lumen/lumen:$ImageTag"

# ────────────────────────────────────────
# Resolve paths
# ────────────────────────────────────────
$rootDir      = $PSScriptRoot
$terraformDir = Join-Path $rootDir "my-terraform"
$tfvarsPath   = Join-Path $terraformDir "terraform.tfvars"
$deployScript = Join-Path $rootDir "deploy.ps1"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   LUMEN -- Deploy Script               " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Image  : $FullImageName"
Write-Host "  Region : $Region"
Write-Host "  Project: $ProjectId"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ────────────────────────────────────────
# Validate paths exist
# ────────────────────────────────────────
if (-not (Test-Path $terraformDir)) {
    Write-Host "[ERROR] Terraform directory not found at $terraformDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $tfvarsPath)) {
    Write-Host "[ERROR] terraform.tfvars not found at $tfvarsPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $deployScript)) {
    Write-Host "[ERROR] deploy.ps1 not found at $deployScript" -ForegroundColor Red
    exit 1
}

# ────────────────────────────────────────
# Step 1 -- Ensure Artifact Registry repository exists
# ────────────────────────────────────────
Write-Host "[REGISTRY] Ensuring Artifact Registry repository exists..." -ForegroundColor Yellow
$repoExists = gcloud artifacts repositories describe lumen --location=$Region --project=$ProjectId 2>$null
if (-not $repoExists) {
    Write-Host "[NEW] Creating Artifact Registry repository 'lumen'..." -ForegroundColor Blue
    gcloud artifacts repositories create lumen `
        --repository-format=docker `
        --location=$Region `
        --project=$ProjectId

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create Artifact Registry repository!" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Repository created" -ForegroundColor Green
} else {
    Write-Host "[OK] Repository already exists" -ForegroundColor Green
}

# ────────────────────────────────────────
# Step 2 -- Authenticate Docker with Artifact Registry
# ────────────────────────────────────────
Write-Host "[AUTH] Configuring Docker for Artifact Registry..." -ForegroundColor Yellow
gcloud auth configure-docker $RegistryHost --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker auth with Artifact Registry failed!" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Docker authenticated with Artifact Registry" -ForegroundColor Green

# ────────────────────────────────────────
# Step 3 -- Docker Build
# ────────────────────────────────────────
Write-Host ""
Write-Host "[BUILD] Building Docker image: $FullImageName" -ForegroundColor Yellow
docker build -t $FullImageName $rootDir

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Docker build successful!" -ForegroundColor Green

# ────────────────────────────────────────
# Step 4 -- Docker Push to Artifact Registry
# ────────────────────────────────────────
Write-Host ""
Write-Host "[PUSH] Pushing image to Artifact Registry: $FullImageName" -ForegroundColor Yellow
docker push $FullImageName

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker push failed!" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Docker push successful!" -ForegroundColor Green

# ────────────────────────────────────────
# Step 5 -- Run deploy.ps1 (terraform import + apply)
# ────────────────────────────────────────
Write-Host ""
Write-Host "[DEPLOY] Running deploy.ps1..." -ForegroundColor Yellow
& $deployScript -ProjectId $ProjectId -ProjectNumber $ProjectNumber -Region $Region -ImageTag $ImageTag

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Deployment failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Full Deploy Complete!                " -ForegroundColor Green
Write-Host "   Image: $FullImageName               " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
