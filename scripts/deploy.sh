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
SKIP_BUILD=${SKIP_BUILD:-"false"}

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
KSA_NAME="${CLUSTER_NAME}-sa"

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
helm upgrade --install cmbcluster  ./helm \
    --namespace $K8S_NAMESPACE \
    --wait \
    --timeout=10m \
    --disable-openapi-validation \
    --set global.projectId=$PROJECT_ID \
    --set ingress.baseDomain=$DOMAIN \
    --set global.registryUrl=$IMAGE_REPO \
    --set global.imageTag=$TAG \
    --set ingress.enabled=true \
    --set ingress.className=nginx \
    --set ingress.tls.enabled=true \
    --set ingress.tls.mainSecretName="$DOMAIN-main-tls" \
    --set ingress.tls.usersSecretName="$DOMAIN-users-wildcard-tls" \
    --set backend.image.repository=$IMAGE_REPO/cmbcluster-backend \
    --set backend.image.tag=$TAG \
    --set frontend.image.repository=$IMAGE_REPO/cmbcluster-frontend \
    --set frontend.image.tag=$TAG \
    --set userEnvironment.image.repository=$IMAGE_REPO/cmbcluster-user-env \
    --set userEnvironment.image.tag=$TAG \
    --set backend.secretName=cmbcluster-backend-secrets \
    --set-string backend.config.tokenExpireHours="$TOKEN_EXPIRE_HOURS" \
    --set-string backend.config.maxInactiveHours="$MAX_INACTIVE_HOURS" \
    --set-string backend.config.maxUserPods="$MAX_USER_PODS" \
    --set-string backend.config.devMode="$DEV_MODE" \
    --set-string backend.config.debug="$DEBUG" \
    --set serviceAccount.name=$KSA_NAME \
    --set workloadIdentity.gsaEmail=$GSA_EMAIL


# Wait for deployments to be ready
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
    deployment/cmbcluster-backend \
    deployment/cmbcluster-frontend \
    -n cmbcluster

# The DOMAIN variable (e.g., "my.domain.com") must be set for this section to work.
# Ensure the script is run after `gcloud auth login` and `gcloud config set project`.

# --- DNS Automation Functions ---

# Function to get the Ingress Load Balancer IP address.
# It will wait for up to 5 minutes for the IP to be assigned.
# Progress messages are sent to stderr, so only the final IP is sent to stdout.
get_ingress_ip() {
  echo "Waiting for Ingress Load Balancer IP..." >&2
  local ip
  # Loop for 30 attempts with a 10-second sleep (5-minute timeout).
  for i in {1..30}; do
    # Fetches the IP from the NGINX ingress controller service.
    # Note: If your ingress controller is in a different namespace, change 'ingress-nginx'.
    ip=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    if [[ -n "$ip" && "$ip" != "<pending>" ]]; then
      echo "Found Ingress IP: $ip" >&2
      echo "$ip"
      return 0
    fi
    echo "Still waiting for IP... (Attempt $i/30)" >&2
    sleep 10
  done
  echo "Error: Timed out waiting for Ingress Load Balancer IP." >&2
  return 1
}

# Function to create or update the DNS A record in Google Cloud DNS.
update_dns_record() {
  local ip_address="$1"
  local domain_name="$2" # This is the FQDN, e.g., myapp.example.com
  # This script assumes the Google Cloud DNS Managed Zone name is the domain name with dots replaced by dashes.
  # e.g., cmbagent.cloud -> cmbagent-cloud
  local dns_zone_name
  dns_zone_name=$(echo "$domain_name" | sed 's/\./-/g')

  echo "Updating DNS for domain '$domain_name' in zone '$dns_zone_name' to point to '$ip_address'..."

  # Get the current IP address from DNS to check if an update is needed.
  local current_ip
  current_ip=$(gcloud dns record-sets list --zone="$dns_zone_name" --name="$domain_name." --type=A --format="value(rrdatas[0])")

  if [[ "$current_ip" == "$ip_address" ]]; then
    echo "DNS record is already up to date. No changes needed."
    return 0
  fi

  # Use a transaction to make the change atomic and safe.
  gcloud dns record-sets transaction start --zone="$dns_zone_name"

  # If a record already exists, remove the old one from the transaction.
  if [[ -n "$current_ip" ]]; then
    echo "Removing old A record pointing to $current_ip..."
    local current_ttl
    current_ttl=$(gcloud dns record-sets list --zone="$dns_zone_name" --name="$domain_name." --type=A --format="value(ttl)")
    gcloud dns record-sets transaction remove --zone="$dns_zone_name" \
      --name="$domain_name." \
      --ttl="$current_ttl" \
      --type=A "$current_ip"
  fi

  # Add the new record to the transaction.
  echo "Adding new A record pointing to $ip_address..."
  gcloud dns record-sets transaction add --zone="$dns_zone_name" \
    --name="$domain_name." \
    --ttl=300 \
    --type=A "$ip_address"

  # Execute the transaction to apply the changes.
  echo "Executing DNS transaction..."
  if gcloud dns record-sets transaction execute --zone="$dns_zone_name"; then
    echo "Successfully updated DNS record for $domain_name."
  else
    echo "Error: Failed to update DNS record. Aborting transaction." >&2
    gcloud dns record-sets transaction abort --zone="$dns_zone_name"
    return 1
  fi
}

# --- Example of how to call these functions in your main script logic ---

# 1. Deploy your Ingress controller and application first.
# ... your helm install/upgrade commands ...

# 2. Get the Ingress IP.
INGRESS_IP=$(get_ingress_ip)
if [[ -z "$INGRESS_IP" ]]; then
  exit 1
fi

# 3. Update the DNS record.
update_dns_record "$INGRESS_IP" "$DOMAIN"
if [[ $? -ne 0 ]]; then
  echo "DNS update failed. Please check permissions and configuration." >&2
  exit 1
fi

echo "DNS automation complete."
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
