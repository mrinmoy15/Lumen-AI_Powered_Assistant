# bootstrap.ps1
# One-time setup: creates the GCP project, links billing, and grants the
# deployer account owner rights so Terraform can provision all resources.
#
# Prerequisites:
#   - gcloud CLI installed and authenticated (gcloud auth login)
#   - Authenticated account must have resourcemanager.projects.create
#     on the target org/folder (or be a free-tier personal account)
#
# Usage:
#   .\bootstrap.ps1 -ProjectId "your-project-id" -BillingAccount "XXXXXX-XXXXXX-XXXXXX"
#   .\bootstrap.ps1 -ProjectId "your-project-id" -BillingAccount "XXXXXX-XXXXXX-XXXXXX" -OrgId "123456789"
#   .\bootstrap.ps1 -ProjectId "your-project-id" -BillingAccount "XXXXXX-XXXXXX-XXXXXX" -SkipBilling

param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [Parameter(Mandatory = $true)]
    [string]$BillingAccount,

    [Parameter(Mandatory = $false)]
    [string]$OrgId,

    [Parameter(Mandatory = $false)]
    [string]$FolderId,

    # Set this flag if your account does not have billing.resourceAssociations.create
    # on the billing account (e.g. org-managed billing). An org/billing admin must
    # link the billing account manually before you run this script.
    [switch]$SkipBilling
)

$PROJECT_ID = $ProjectId
$DEPLOYER   = gcloud config get-value account 2>$null

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   LUMEN -- GCP Bootstrap               " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Project : $PROJECT_ID"
Write-Host "  Deployer: $DEPLOYER"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# -- 1. Check / create project -------------------------------------------------
Write-Host "[PROJECT] Checking if project '$PROJECT_ID' already exists..." -ForegroundColor Yellow
$existing = gcloud projects describe $PROJECT_ID --format="value(projectId)" 2>$null
if ($existing -eq $PROJECT_ID) {
    Write-Host "[OK] Project already exists -- skipping creation." -ForegroundColor Green
} else {
    Write-Host "[NEW] Creating project '$PROJECT_ID'..." -ForegroundColor Blue

    $createArgs = @("projects", "create", $PROJECT_ID, "--name=$PROJECT_ID")
    if ($OrgId)    { $createArgs += "--organization=$OrgId" }
    elseif ($FolderId) { $createArgs += "--folder=$FolderId" }

    gcloud @createArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create project. Ensure your account has resourcemanager.projects.create permission." -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Project created." -ForegroundColor Green
}

# -- 2. Link billing account ---------------------------------------------------
if ($SkipBilling) {
    Write-Host "[SKIP] Skipping billing link (-SkipBilling set)." -ForegroundColor Yellow
    Write-Host "  ACTION REQUIRED: Ask your org/billing admin to run:"
    Write-Host "    gcloud billing projects link $PROJECT_ID --billing-account=$BillingAccount"
    Write-Host "  Then re-run this script with -SkipBilling to complete IAM setup."
} else {
    Write-Host "[BILLING] Linking billing account '$BillingAccount'..." -ForegroundColor Yellow
    gcloud billing projects link $PROJECT_ID --billing-account=$BillingAccount
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "[ERROR] Could not link billing account. Your account likely lacks" -ForegroundColor Red
        Write-Host "        'billing.resourceAssociations.create' on billing account '$BillingAccount'." -ForegroundColor Red
        Write-Host ""
        Write-Host "  Options:"
        Write-Host "    A) Ask your org/billing admin to run:"
        Write-Host "         gcloud billing projects link $PROJECT_ID --billing-account=$BillingAccount"
        Write-Host "       Then re-run: make bootstrap-gcp"
        Write-Host ""
        Write-Host "    B) Link it yourself in the GCP Console:"
        Write-Host "         Console -> Billing -> My Projects -> Link a project -> '$PROJECT_ID'"
        Write-Host "       Then re-run: make bootstrap-gcp"
        Write-Host ""
        Write-Host "    C) If billing is already linked, skip this step:"
        Write-Host "         make bootstrap-gcp SKIP_BILLING=1"
        exit 1
    }
    Write-Host "[OK] Billing account linked." -ForegroundColor Green
}

# -- 3. Grant deployer roles/owner ---------------------------------------------
# Owner is required so Terraform can self-manage IAM, enable APIs, create
# Cloud SQL, Artifact Registry, Secret Manager secrets, and Cloud Run services.
Write-Host "[IAM] Granting roles/owner to '$DEPLOYER'..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="user:$DEPLOYER" `
    --role="roles/owner"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to grant IAM role. The account running this script must have resourcemanager.projects.setIamPolicy on the project." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] roles/owner granted to $DEPLOYER." -ForegroundColor Green

# -- 4. Enable core APIs needed before Terraform init -------------------------
# Terraform itself needs these APIs to exist before it can plan/apply.
Write-Host "[APIs] Enabling prerequisite APIs..." -ForegroundColor Yellow
$apis = @(
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "serviceusage.googleapis.com"
)
foreach ($api in $apis) {
    Write-Host "  enabling $api..."
    gcloud services enable $api --project=$PROJECT_ID --quiet
}
Write-Host "[OK] Prerequisite APIs enabled." -ForegroundColor Green

# -- 5. Summary ----------------------------------------------------------------
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Bootstrap complete!                  " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Authenticate for Terraform:"
Write-Host "       gcloud auth application-default login"
Write-Host "  2. Deploy infrastructure + application:"
Write-Host "       make deploy-image"
Write-Host ""
