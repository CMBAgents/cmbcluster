#!/bin/bash

# ============================================================================
# AWS ECR Build and Push Script for CMBCluster
# ============================================================================
#
# This script builds Docker images and pushes them to Amazon ECR.
#
# Prerequisites:
#   - AWS CLI v2 installed and configured
#   - Docker installed and running
#   - ECR repositories created (by setup-cluster.sh)
#   - Appropriate AWS permissions
#
# Usage:
#   ./scripts/aws/build-images.sh [TAG]
#
# Examples:
#   ./scripts/aws/build-images.sh latest
#   ./scripts/aws/build-images.sh v1.0.0
#   ./scripts/aws/build-images.sh  # Uses 'latest' tag
#
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Load configuration from .env file
load_config() {
    if [ -f "$PROJECT_ROOT/.env" ]; then
        log_info "Loading configuration from .env file..."
        export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
    else
        log_error ".env file not found at $PROJECT_ROOT/.env"
        exit 1
    fi
}

# Load configuration
cd "$PROJECT_ROOT"
load_config

# Configuration with defaults
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID}"
EKS_CLUSTER_NAME="${EKS_CLUSTER_NAME:-cmbcluster-eks}"
IMAGE_TAG="${1:-${IMAGE_TAG:-latest}}"

# Validate required variables
if [ -z "$AWS_ACCOUNT_ID" ]; then
    log_error "AWS_ACCOUNT_ID is not set. Please configure it in .env"
    exit 1
fi

# ECR registry URL
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

log_info "==================================="
log_info "AWS ECR Build Configuration"
log_info "==================================="
log_info "AWS Region: $AWS_REGION"
log_info "AWS Account ID: $AWS_ACCOUNT_ID"
log_info "EKS Cluster: $EKS_CLUSTER_NAME"
log_info "ECR Registry: $ECR_REGISTRY"
log_info "Image Tag: $IMAGE_TAG"
log_info "==================================="

# Check prerequisites
log_info "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    log_error "AWS CLI not found. Please install AWS CLI v2."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    log_error "Docker not found. Please install Docker."
    exit 1
fi

if ! docker info &> /dev/null; then
    log_error "Docker daemon is not running. Please start Docker."
    exit 1
fi

log_success "Prerequisites check passed"

# Authenticate to ECR
log_info "Authenticating to Amazon ECR..."
aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "$ECR_REGISTRY"

if [ $? -eq 0 ]; then
    log_success "Successfully authenticated to ECR"
else
    log_error "Failed to authenticate to ECR"
    exit 1
fi

# Build and push backend image
log_info ""
log_info "Building backend image..."

BACKEND_IMAGE="${ECR_REGISTRY}/${EKS_CLUSTER_NAME}-backend:${IMAGE_TAG}"

docker build \
    -t "$BACKEND_IMAGE" \
    -f "$PROJECT_ROOT/backend/Dockerfile" \
    "$PROJECT_ROOT/backend"

if [ $? -eq 0 ]; then
    log_success "Backend image built successfully"
else
    log_error "Failed to build backend image"
    exit 1
fi

log_info "Pushing backend image to ECR..."
docker push "$BACKEND_IMAGE"

if [ $? -eq 0 ]; then
    log_success "Backend image pushed: $BACKEND_IMAGE"
else
    log_error "Failed to push backend image"
    exit 1
fi

# Build and push frontend image
log_info ""
log_info "Building frontend image..."

FRONTEND_IMAGE="${ECR_REGISTRY}/${EKS_CLUSTER_NAME}-frontend:${IMAGE_TAG}"

docker build \
    -t "$FRONTEND_IMAGE" \
    -f "$PROJECT_ROOT/nextjs-frontend/Dockerfile" \
    "$PROJECT_ROOT/nextjs-frontend"

if [ $? -eq 0 ]; then
    log_success "Frontend image built successfully"
else
    log_error "Failed to build frontend image"
    exit 1
fi

log_info "Pushing frontend image to ECR..."
docker push "$FRONTEND_IMAGE"

if [ $? -eq 0 ]; then
    log_success "Frontend image pushed: $FRONTEND_IMAGE"
else
    log_error "Failed to push frontend image"
    exit 1
fi

# Summary
log_info ""
log_info "==================================="
log_info "Build and Push Complete"
log_info "==================================="
log_success "Backend Image: $BACKEND_IMAGE"
log_success "Frontend Image: $FRONTEND_IMAGE"
log_info "==================================="
log_info ""
log_info "Next Steps:"
log_info "1. Deploy to EKS: ./scripts/aws/deploy.sh"
log_info "2. Check deployment status: kubectl get pods -n ${NAMESPACE:-cmbcluster}"
log_info ""

log_success "Build and push completed successfully!"
