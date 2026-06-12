# Load environment variables from .env
include .env
export

# Variables
VERSION = $(APP_VERSION)

.PHONY: build run down logs clean bootstrap-gcp deploy-image destroy

## Build and start all containers locally
build:
	docker compose up --build

## Run containers without rebuilding
run:
	docker compose up

## Stop and remove containers
down:
	docker compose down

## View container logs
logs:
	docker compose logs -f

## Remove local image from Artifact Registry cache
clean:
	docker rmi $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/$(APP_NAME)/$(APP_NAME):$(VERSION)

## One-time: create GCP project, link billing, grant deployer owner IAM
## If your account cannot link billing (org-managed), use: make bootstrap-gcp SKIP_BILLING=1
bootstrap-gcp:
	powershell -ExecutionPolicy Bypass -File ./my-terraform/bootstrap.ps1 \
		-ProjectId "$(GCP_PROJECT_ID)" \
		-BillingAccount "$(BILLING_ACCOUNT)" \
		$(if $(SKIP_BILLING),-SkipBilling,)

## Build image, push to Artifact Registry, and deploy to Cloud Run via Terraform
deploy-image:
	powershell -ExecutionPolicy Bypass -File ./deploy.ps1 \
		-ProjectId "$(GCP_PROJECT_ID)" \
		-ProjectNumber "$(GCP_PROJECT_NUMBER)" \
		-Region "$(GCP_REGION)" \
		-ImageTag "$(VERSION)" \
		-AppName "$(APP_NAME)"

## Tear down all GCP infrastructure (zero ongoing cost)
destroy:
	cd my-terraform && terraform destroy -auto-approve
