#!/bin/bash
# Re-tag and push Denario image to the correct registry

set -e

PROJECT_ID="cmbcluster"
OLD_REGISTRY="us-central1-docker.pkg.dev/$PROJECT_ID/cmbcluster-dev-images"
NEW_REGISTRY="us-central1-docker.pkg.dev/$PROJECT_ID/cmbcluster-images"
IMAGE_NAME="denario"
TAG="latest"

OLD_IMAGE="$OLD_REGISTRY/$IMAGE_NAME:$TAG"
NEW_IMAGE="$NEW_REGISTRY/$IMAGE_NAME:$TAG"

echo "Re-tagging Denario image from old registry to new registry..."
echo "Old: $OLD_IMAGE"
echo "New: $NEW_IMAGE"

# Tag the image
docker tag "$OLD_IMAGE" "$NEW_IMAGE"

# Authenticate to new registry
echo "Authenticating to new registry..."
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

# Push to new registry
echo "Pushing to new registry..."
docker push "$NEW_IMAGE"

echo "✅ Successfully re-tagged and pushed Denario image!"
echo ""
echo "Image is now available at:"
echo "  $NEW_IMAGE"
