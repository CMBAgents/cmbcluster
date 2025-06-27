#!/bin/bash
set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}
DOMAIN=${2:-"cmbcluster.example.com"}
TAG=${3:-"latest"}
SKIP_BUILD=${4:-"false"}

if [ -z "$PROJECT_ID" ] || [ -z "$DOMAIN" ]; then
    echo "Error: PROJECT_ID and DOMAIN are required"
    echo "Usage: $0 <PROJECT_ID> <DOMAIN> [TAG]"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi


echo "🚀 Deploying CMBCluster..."
echo "Project: $PROJECT_ID"
echo "Domain: $DOMAIN"
echo "Tag: $TAG"
echo "Skip Build: $SKIP_BUILD"

# Ensure we have cluster access
gcloud container clusters get-credentials cmbcluster --zone=us-central1-b --project=$PROJECT_ID

# Conditionally build images
if [ "$SKIP_BUILD" != "true" ]; then
    echo "🏗️ Building images..."
    ./scripts/build-images.sh $PROJECT_ID $TAG
else
    echo "⏭️ Skipping image build..."
fi

# Create namespace
kubectl create namespace cmbcluster --dry-run=client -o yaml | kubectl apply -f - --validate=false

# Create secrets
echo "🔐 Creating secrets..."
kubectl create secret generic cmbcluster-secrets \
    --from-literal=google-client-id="${GOOGLE_CLIENT_ID}" \
    --from-literal=google-client-secret="${GOOGLE_CLIENT_SECRET}" \
    --from-literal=secret-key="${SECRET_KEY}" \
    --namespace=cmbcluster \
    --dry-run=client -o yaml | kubectl apply -f - --validate=false

# Deploy using Helm
echo "⚙️ Deploying with Helm..."
helm upgrade --install cmbcluster ./helm \
    --namespace cmbcluster \
    --set global.projectId=$PROJECT_ID \
    --set global.domain=$DOMAIN \
    --set backend.image.tag=$TAG \
    --set frontend.image.tag=$TAG \
    --set userEnvironment.image.tag=$TAG \
    --wait \
    --timeout=10m \
    --disable-openapi-validation

# Wait for deployments to be ready
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
    deployment/cmbcluster-backend \
    deployment/cmbcluster-frontend \
    -n cmbcluster

echo "✅ CMBCluster deployed successfully!"
echo ""
echo "🌐 Access your deployment:"
echo "Frontend: https://$DOMAIN"
echo "API: https://api.$DOMAIN"
echo "Docs: https://api.$DOMAIN/docs"
echo ""
echo "📋 Useful commands:"
echo "kubectl get pods -n cmbcluster"
echo "kubectl logs -f deployment/cmbcluster-backend -n cmbcluster"
echo "kubectl logs -f deployment/cmbcluster-frontend -n cmbcluster"
echo ""
echo "🔍 Get ingress IP:"
echo "kubectl get ingress -n cmbcluster"
