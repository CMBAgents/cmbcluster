#!/bin/bash
set -e

# --- Configuration Loading ---
# 1. Load defaults from .env file if it exists.
# 2. Allow overrides from command-line arguments.
# 3. Set final defaults for any remaining unset variables.

# Use a more robust method to load .env file. This handles special characters.
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env file..."
    set -o allexport
    source .env
    set +o allexport
fi

# --- Variable Definitions & Precedence ---
# Command-line arguments override .env file values.
PROJECT_ID=${1:-$PROJECT_ID}
CLUSTER_NAME=${2:-$CLUSTER_NAME}
DOMAIN=${3:-$DOMAIN}
REGION=${4:-$REGION}
ZONE=${5:-$ZONE}
TAG=${6:-$TAG}
SKIP_BUILD=${7:-$SKIP_BUILD}

# Set final defaults if variables are still not set
PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project)}
CLUSTER_NAME=${CLUSTER_NAME:-"cmbcluster"}
REGION=${REGION:-"us-central1"}
ZONE=${ZONE:-"${ZONE}"}
TAG=${TAG:-"latest"}
SKIP_BUILD=${SKIP_BUILD:-"true"}

# Validate required variables
if [ -z "$PROJECT_ID" ] || [ -z "$DOMAIN" ]; then
    echo "Error: PROJECT_ID and DOMAIN are required. Set them in .env or pass as arguments."
    echo "Usage: $0 [PROJECT_ID] [CLUSTER_NAME] [DOMAIN] [REGION] [ZONE] [TAG] [SKIP_BUILD]"
    exit 1
fi

# Define derived variables
IMAGE_REPO="${REGION}-docker.pkg.dev/${PROJECT_ID}/${CLUSTER_NAME}-images"
K8S_NAMESPACE=${NAMESPACE:-$CLUSTER_NAME} # Use NAMESPACE from .env or default to CLUSTER_NAME

echo "🚀 Deploying CMBCluster with the following configuration:"
echo "--------------------------------------------------"
echo "Project:         $PROJECT_ID"
echo "Cluster:         $CLUSTER_NAME"
echo "Region:          $REGION"
echo "Zone:            $ZONE"
echo "Domain:          $DOMAIN"
echo "Image Repo:      $IMAGE_REPO"
echo "Image Tag:       $TAG"
echo "Skip Build:      $SKIP_BUILD"
echo "K8s Namespace:   $K8S_NAMESPACE"
echo "--------------------------------------------------"

# Ensure we have cluster access (using the same zone as setup-cluster.sh)
gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE --project=$PROJECT_ID

# --- Workload Identity Setup ---
echo "🔑 Setting up Workload Identity bindings..."

# Define service account names, ensuring they match setup-cluster.sh
GSA_NAME="${CLUSTER_NAME}-workload-sa"
GSA_EMAIL="${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KSA_NAME="${CLUSTER_NAME}-ksa"

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
# Create a secret for the backend. The keys must be uppercase to be correctly
# mapped to environment variables by the Helm chart's 'envFrom' directive.
kubectl create secret generic cmbcluster-backend-secrets \
    --from-literal=GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID}" \
    --from-literal=GOOGLE_CLIENT_SECRET="${GOOGLE_CLIENT_SECRET}" \
    --from-literal=SECRET_KEY="${SECRET_KEY:-$(openssl rand -hex 32)}" \
    --namespace=$K8S_NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

# Deploy using Helm
echo "⚙️ Deploying with Helm..."
# Pass configuration from .env and other scripts to the Helm chart.
# This ensures the backend gets all required environment variables and prevents Pydantic validation errors.
helm upgrade --install cmbcluster ./helm \
    --namespace $K8S_NAMESPACE \
    --wait \
    --timeout=10m \
    --disable-openapi-validation \
    --set global.projectId=$PROJECT_ID \
    --set global.domain=$DOMAIN \
    --set global.imageRegistry=$IMAGE_REPO \
    --set global.imageTag=$TAG \
    --set ingress.enabled=true \
    --set ingress.className=nginx \
    --set ingress.tls.enabled=true \
    --set ingress.tls.secretName="$DOMAIN-tls" \
    --set ingress.tls.clusterIssuer=letsencrypt-prod \
    --set backend.image.repository=$IMAGE_REPO/cmbcluster-backend \
    --set backend.image.tag=$TAG \
    --set frontend.image.repository=$IMAGE_REPO/cmbcluster-frontend \
    --set frontend.image.tag=$TAG \
    --set userEnvironment.image.repository=$IMAGE_REPO/cmbcluster-user-env \
    --set userEnvironment.image.tag=$TAG \
    --set frontend.service.port=8501 \
    --set backend.service.port=8000 \
    --set backend.secretName=cmbcluster-backend-secrets \
    --set-string backend.config.apiUrl="$API_URL" \
    --set-string backend.config.frontendUrl="$FRONTEND_URL" \
    --set-string backend.config.tokenExpireHours="$TOKEN_EXPIRE_HOURS" \
    --set-string backend.config.maxInactiveHours="$MAX_INACTIVE_HOURS" \
    --set-string backend.config.maxUserPods="$MAX_USER_PODS" \
    --set-string backend.config.devMode="$DEV_MODE" \
    --set-string backend.config.debug="$DEBUG" \
    --set serviceAccount.name=$KSA_NAME \
    --set serviceAccount.create=true \
    --set workloadIdentity.gsaEmail=$GSA_EMAIL

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
