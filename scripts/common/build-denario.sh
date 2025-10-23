#!/bin/bash
set -e

# Build and push custom Denario image for CMBCluster

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

echo "🏗️ Building custom Denario image..."
echo "Project: $PROJECT_ID"
echo "Repository: $IMAGE_REPO"
echo "Tag: $TAG"

# Authenticate Docker with Google Artifact Registry
echo "🔐 Authenticating Docker with Artifact Registry..."
REGISTRY_HOSTNAME=$(echo "$IMAGE_REPO" | cut -d'/' -f1)
gcloud auth configure-docker "$REGISTRY_HOSTNAME" --quiet

CONTEXT_PATH="$PROJECT_ROOT/docker/denario"
IMAGE_NAME="denario"
FULL_IMAGE_TAG="$IMAGE_REPO/$IMAGE_NAME:$TAG"

echo "--------------------------------------------------"
echo "📦 Building Denario image: $FULL_IMAGE_TAG"
docker build --no-cache -t "$FULL_IMAGE_TAG" "$CONTEXT_PATH"

echo "🚀 Pushing Denario image..."
docker push "$FULL_IMAGE_TAG"

echo "✅ Denario image built and pushed successfully!"
echo ""
echo "📋 Image: $FULL_IMAGE_TAG"
echo ""
echo "To use this image in your application, update the image_path in the admin panel to:"
echo "  $FULL_IMAGE_TAG"
echo ""
echo "Or for denario specifically:"
echo "  us-central1-docker.pkg.dev/cmbcluster/cmbcluster-images/denario:latest"
