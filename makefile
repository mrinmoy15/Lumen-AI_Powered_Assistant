# Load environment variables from .env
include .env
export

# Variables
VERSION = $(APP_VERSION)

.PHONY: build run down logs clean deploy-image deploy-initial destroy

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

## Remove local image
clean:
	docker rmi us-central1-docker.pkg.dev/$(GCP_PROJECT_ID)/lumen/lumen:$(VERSION)

## Build, push to Artifact Registry and deploy updated image to Cloud Run
deploy-image:
	powershell -ExecutionPolicy Bypass -File ./new_image_deploy.ps1 \
		-ProjectId "$(GCP_PROJECT_ID)" \
		-ProjectNumber "$(GCP_PROJECT_NUMBER)" \
		-Region "$(GCP_REGION)" \
		-ImageTag "$(VERSION)"

## Tear down all GCP infrastructure (zero ongoing cost)
destroy:
	cd my-terraform && terraform destroy -auto-approve

## First-time full deploy: build, push, Terraform apply
deploy-initial:
	powershell -ExecutionPolicy Bypass -File ./new_image_deploy.ps1 \
		-ProjectId "$(GCP_PROJECT_ID)" \
		-ProjectNumber "$(GCP_PROJECT_NUMBER)" \
		-Region "$(GCP_REGION)" \
		-ImageTag "$(VERSION)"