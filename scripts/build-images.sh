#!/bin/bash
set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}
TAG=${2:-"latest"}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is required"
    echo "Usage: $0 <PROJECT_ID> [TAG]"
    exit 1
fi

echo "🏗️ Building CMBCluster images..."
echo "Project: $PROJECT_ID"
echo "Tag: $TAG"

# Configure Docker for GCR
gcloud auth configure-docker

# Build backend image
echo "📦 Building backend image..."
cd backend
docker build -t gcr.io/$PROJECT_ID/cmbcluster-backend:$TAG .
docker push gcr.io/$PROJECT_ID/cmbcluster-backend:$TAG
cd ..

# Build frontend image
echo "📦 Building frontend image..."
cd frontend
docker build -t gcr.io/$PROJECT_ID/cmbcluster-frontend:$TAG .
docker push gcr.io/$PROJECT_ID/cmbcluster-frontend:$TAG
cd ..

# Build user environment image
echo "📦 Building user environment image..."
cd user-environment
docker build -t gcr.io/$PROJECT_ID/cmbcluster-user-env:$TAG .
docker push gcr.io/$PROJECT_ID/cmbcluster-user-env:$TAG
cd ..

echo "✅ All images built and pushed successfully!"
echo ""
echo "📋 Built images:"
echo "- gcr.io/$PROJECT_ID/cmbcluster-backend:$TAG"
echo "- gcr.io/$PROJECT_ID/cmbcluster-frontend:$TAG"
echo "- gcr.io/$PROJECT_ID/cmbcluster-user-env:$TAG"
