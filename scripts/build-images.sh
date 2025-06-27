#!/bin/bash
set -e

# --- Determine script location and project root ---
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

PROJECT_ID=${1:-$(gcloud config get-value project)}
TAG=${2:-"latest"}
IMAGE_REPO=${3:-"us-central1-docker.pkg.dev/$PROJECT_ID/cmbcluster-images"}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is required"
    echo "Usage: $0 <PROJECT_ID> [TAG] [IMAGE_REPO]"
    exit 1
fi

echo "🏗️ Building CMBCluster images..."
echo "Project: $PROJECT_ID"
echo "Repository: $IMAGE_REPO"
echo "Tag: $TAG"

# Build backend image
echo "📦 Building backend image..."
gcloud builds submit "$PROJECT_ROOT/backend" --tag "$IMAGE_REPO/cmbcluster-backend:$TAG" --project=$PROJECT_ID

# Build frontend image
echo "📦 Building frontend image..."
gcloud builds submit "$PROJECT_ROOT/frontend" --tag "$IMAGE_REPO/cmbcluster-frontend:$TAG" --project=$PROJECT_ID

# Build user environment image
echo "📦 Building user environment image..."
gcloud builds submit "$PROJECT_ROOT/user-environment" --tag "$IMAGE_REPO/cmbcluster-user-env:$TAG" --project=$PROJECT_ID

echo "✅ All images built and pushed successfully!"
echo ""
echo "📋 Built images:"
echo "- $IMAGE_REPO/cmbcluster-backend:$TAG"
echo "- $IMAGE_REPO/cmbcluster-frontend:$TAG"
echo "- $IMAGE_REPO/cmbcluster-user-env:$TAG"
