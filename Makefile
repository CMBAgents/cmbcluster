# Use bash for all shell commands
SHELL := /bin/bash

# Ensure the .env file is loaded and its variables are exported to the shell.
# This makes variables like PROJECT_ID, CLUSTER_NAME, etc., available to the scripts.
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Default command: show help
.DEFAULT_GOAL := help

# Phony targets are not real files
.PHONY: help up down logs build deploy setup cleanup add-ip test logs-gke

## --------------------------------------
## General
## --------------------------------------

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

## --------------------------------------
## Local Development (Docker Compose)
## --------------------------------------

up: ## Start all local services with Docker Compose
	@echo "🚀 Starting local development environment..."
	@docker compose up --build -d

down: ## Stop and remove all local services
	@echo "🛑 Stopping local development environment..."
	@docker compose down

logs: ## View logs for all local services
	@echo "📜 Tailing logs for local services..."
	@docker compose logs -f

## --------------------------------------
## Cloud Deployment (GKE)
## --------------------------------------

build: ## Build and push container images to Artifact Registry
	@echo "📦 Building and pushing images..."
	@./scripts/build-images.sh

deploy: ## Deploy the application to the GKE cluster
	@echo "⚙️ Deploying to GKE cluster '$(CLUSTER_NAME)'..."
	@./scripts/deploy.sh

setup: ## Create the GKE cluster and all required infrastructure
	@echo "🏗️ Setting up GKE infrastructure..."
	@./scripts/setup-cluster.sh

cleanup: ## Tear down the GKE cluster and all associated resources
	@echo "🔥 Tearing down all GKE infrastructure..."
	@./scripts/cleanup.sh

add-ip: ## Add your current IP to the GKE master authorized networks list
	@echo "🌐 Adding current IP to authorized networks..."
	@./scripts/add-authorized-ip.sh

test: ## Run tests
	@echo "Running tests..."
	cd backend && python -m pytest

logs-gke: ## View backend logs from the GKE cluster
	@echo "📜 Tailing backend logs from namespace '$(NAMESPACE)'..."
	kubectl logs -f deployment/cmbcluster-backend -n $(NAMESPACE)
