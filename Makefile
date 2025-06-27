.PHONY: help dev build deploy clean setup test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev: ## Start local development environment
	@echo "Starting CMBCluster development environment..."
	docker compose up --build

build: ## Build all Docker images
	@echo "Building CMBCluster images..."
	./scripts/build-images.sh $(PROJECT_ID)

setup: ## Setup GKE cluster and infrastructure
	@echo "Setting up CMBCluster infrastructure..."
	./scripts/setup-cluster.sh $(PROJECT_ID)

deploy: ## Deploy to Kubernetes
	@echo "Deploying CMBCluster..."
	./scripts/deploy.sh $(PROJECT_ID) $(DOMAIN) latest $(SKIP_BUILD)
	

test: ## Run tests
	@echo "Running tests..."
	cd backend && python -m pytest
	cd frontend && streamlit run main.py --server.headless true &

clean: ## Clean up resources
	@echo "Cleaning up CMBCluster resources..."
	./scripts/cleanup.sh $(PROJECT_ID)

logs: ## View application logs
	kubectl logs -f deployment/cmbcluster-backend -n cmbcluster
