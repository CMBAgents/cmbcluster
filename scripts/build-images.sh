#!/bin/bash
set -e

# --- Determine script location and project root ---
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

PROJECT_ID=${1:-$(gcloud config get-value project)}
TAG=${2:-"latest"}
IMAGE_REPO=${3:-"us-central1-docker.pkg.dev/$PROJECT_ID/cmbcluster-dev-images"}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is required"
    echo "Usage: $0 <PROJECT_ID> [TAG] [IMAGE_REPO]"
    exit 1
fi

echo "🏗️ Building CMBCluster images..."
echo "Project: $PROJECT_ID"
echo "Repository: $IMAGE_REPO"
echo "Tag: $TAG"

# Authenticate Docker with Google Artifact Registry for the target region
echo "🔐 Authenticating Docker with Artifact Registry..."
REGISTRY_HOSTNAME=$(echo "$IMAGE_REPO" | cut -d'/' -f1)
gcloud auth configure-docker "$REGISTRY_HOSTNAME" --quiet

#SERVICES=("backend" "frontend" "user-environment")

# SERVICES=("frontend")
#  SERVICES=("backend" )
SERVICES=("frontend" "backend")
for SERVICE in "${SERVICES[@]}"; do
    # Use nextjs-frontend directory for frontend service
    if [ "$SERVICE" == "frontend" ]; then
        CONTEXT_PATH="$PROJECT_ROOT/nextjs-frontend"
    else
        CONTEXT_PATH="$PROJECT_ROOT/$SERVICE"
    fi
    
    IMAGE_NAME="cmbcluster-$SERVICE"
    FULL_IMAGE_TAG="$IMAGE_REPO/$IMAGE_NAME:$TAG"

    echo "--------------------------------------------------"
    echo "📦 Building $SERVICE image locally: $FULL_IMAGE_TAG"
    docker build --no-cache -t "$FULL_IMAGE_TAG" "$CONTEXT_PATH"

    echo "🚀 Pushing $SERVICE image..."
    docker push "$FULL_IMAGE_TAG"
done

echo "✅ All images built and pushed successfully!"
echo ""
echo "📋 Built images:"
echo "- $IMAGE_REPO/cmbcluster-backend:$TAG"
echo "- $IMAGE_REPO/cmbcluster-frontend:$TAG"
echo "- $IMAGE_REPO/cmbcluster-user-env:$TAG"
