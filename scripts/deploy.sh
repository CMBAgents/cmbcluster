#!/bin/bash
set -e

# Configuration - should match setup-cluster.sh for consistency
PROJECT_ID=${1:-$(gcloud config get-value project)}
CLUSTER_NAME=${2:-"cmbcluster"}
DOMAIN=${3:-"cmbcluster.34.16.97.178.nip.io"}
REGION=${4:-"us-central1"}
ZONE=${5:-"us-central1-a"}
TAG=${6:-"latest"}
SKIP_BUILD=${7:-"true"} # Default to building images unless specified

if [ -z "$PROJECT_ID" ] || [ -z "$DOMAIN" ]; then
    echo "Error: PROJECT_ID and DOMAIN are required"
    echo "Usage: $0 <PROJECT_ID> [CLUSTER_NAME] [DOMAIN] [REGION] [ZONE] [TAG] [SKIP_BUILD]"
    exit 1

fi

# Define derived variables early
IMAGE_REPO="${REGION}-docker.pkg.dev/${PROJECT_ID}/${CLUSTER_NAME}-images"

echo "🚀 Deploying CMBCluster..."
echo "Project: $PROJECT_ID"
echo "Domain: $DOMAIN"
echo "Cluster: $CLUSTER_NAME"
echo "Image Repo: $IMAGE_REPO"
echo "Tag: $TAG"
echo "Skip Build: $SKIP_BUILD"

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Ensure we have cluster access (using the same zone as setup-cluster.sh)
gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE --project=$PROJECT_ID

# --- Workload Identity Setup ---
echo "🔑 Setting up Workload Identity bindings..."

# Define service account names, ensuring they match setup-cluster.sh
GSA_NAME="${CLUSTER_NAME}-workload-sa"
GSA_EMAIL="${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KSA_NAME="${CLUSTER_NAME}-ksa"
K8S_NAMESPACE=$CLUSTER_NAME

# Allow the Kubernetes Service Account to impersonate the Google Service Account.
# This is the core of Workload Identity. It grants the KSA the 'workloadIdentityUser' role on the GSA.
echo "Binding KSA '$KSA_NAME' to GSA '$GSA_EMAIL'..."
gcloud iam service-accounts add-iam-policy-binding $GSA_EMAIL \
    --role="roles/iam.workloadIdentityUser" \
    --member="serviceAccount:${PROJECT_ID}.svc.id.goog[${K8S_NAMESPACE}/${KSA_NAME}]" \
    --project=$PROJECT_ID \
    --quiet || echo "✅ IAM policy binding already exists."

# Conditionally build images
if [ "$SKIP_BUILD" != "true" ]; then
    echo "🏗️ Building images..."
    ./scripts/build-images.sh $PROJECT_ID $TAG $IMAGE_REPO
else
    echo "⏭️ Skipping image build..."
fi

# Create namespace
kubectl create namespace $K8S_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create secrets
echo "🔐 Creating secrets..."
kubectl create secret generic cmbcluster-secrets \
    --from-literal=google-client-id="${GOOGLE_CLIENT_ID}" \
    --from-literal=google-client-secret="${GOOGLE_CLIENT_SECRET}" \
    --from-literal=secret-key="${SECRET_KEY:-$(openssl rand -hex 32)}" \
    --namespace=$K8S_NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

# Deploy using Helm
echo "⚙️ Deploying with Helm..."
helm upgrade --install cmbcluster ./helm \
    --namespace $K8S_NAMESPACE \
    --set global.projectId=$PROJECT_ID \
    --set ingress.enabled=true \
    --set ingress.className=nginx \
    --set ingress.tls.enabled=true \
    --set ingress.tls.secretName="$DOMAIN-tls" \
    --set frontend.service.port=8501 \
    --set backend.service.port=8000 \
    --set backend.config.maxInactiveHours=24 \
    --set ingress.tls.clusterIssuer=letsencrypt-prod \
    --set backend.image.repository=$IMAGE_REPO/cmbcluster-backend \
    --set frontend.image.repository=$IMAGE_REPO/cmbcluster-frontend \
    --set userEnvironment.image.repository=$IMAGE_REPO/cmbcluster-user-env \
    --set global.domain=$DOMAIN \
    --set backend.image.tag=$TAG \
    --set frontend.image.tag=$TAG \
    --set userEnvironment.image.tag=$TAG \
    --set serviceAccount.name=$KSA_NAME \
    --set serviceAccount.create=true \
    --set workloadIdentity.gsaEmail=$GSA_EMAIL \
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
