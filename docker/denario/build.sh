#!/bin/bash

# Build script for custom Denario image with CMBCluster support

set -e

# Get the project ID and registry from env or use defaults
PROJECT_ID=${PROJECT_ID:-"cmbcluster"}
REGISTRY_URL=${REGISTRY_URL:-"gcr.io/${PROJECT_ID}"}
IMAGE_NAME="denario"
IMAGE_TAG=${IMAGE_TAG:-"latest"}

echo "Building custom Denario image..."
echo "Registry: ${REGISTRY_URL}"
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"

# Navigate to the directory containing the Dockerfile
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# Build the image
docker build -t "${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}" .

echo "Build complete!"
echo "To push the image, run:"
echo "  docker push ${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "Or use the main build script:"
echo "  cd ../.. && ./scripts/build-images.sh denario"
