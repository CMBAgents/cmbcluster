#!/bin/bash
set -e

# Parse command line arguments
FORCE_REBUILD=false
if [ "$1" = "--force-rebuild" ] || [ "$1" = "-f" ]; then
    FORCE_REBUILD=true
    echo "🔄 Force rebuild mode enabled"
fi

# --- Security Configuration Validation ---
echo "🔒 Validating security configuration for production deployment..."

# Function to validate security requirements
validate_security_config() {
    local errors=0
    
    echo "Checking required security environment variables..."
    
    # Check critical security variables
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" == "dev-secret-key-change-in-production" ]; then
        echo "❌ ERROR: SECRET_KEY not set or using development default"
        echo "   Generate a secure key: openssl rand -hex 32"
        errors=$((errors + 1))
    elif [ ${#SECRET_KEY} -lt 32 ]; then
        echo "❌ ERROR: SECRET_KEY too short (minimum 32 characters required)"
        errors=$((errors + 1))
    else
        echo "✅ SECRET_KEY configured securely"
    fi
    
    if [ -z "$GOOGLE_CLIENT_ID" ]; then
        echo "❌ ERROR: GOOGLE_CLIENT_ID not configured"
        echo "   Configure Google OAuth in Google Cloud Console"
        errors=$((errors + 1))
    else
        echo "✅ GOOGLE_CLIENT_ID configured"
    fi
    
    if [ -z "$GOOGLE_CLIENT_SECRET" ]; then
        echo "❌ ERROR: GOOGLE_CLIENT_SECRET not configured"
        echo "   Configure Google OAuth in Google Cloud Console"
        errors=$((errors + 1))
    else
        echo "✅ GOOGLE_CLIENT_SECRET configured"
    fi
    
    if [ -z "$NEXTAUTH_SECRET" ] || [ "$NEXTAUTH_SECRET" == "your-secret-key-here-replace-in-production" ]; then
        echo "❌ ERROR: NEXTAUTH_SECRET not set or using development default"
        echo "   Generate a secure key: openssl rand -base64 32"
        errors=$((errors + 1))
    elif [ ${#NEXTAUTH_SECRET} -lt 32 ]; then
        echo "❌ ERROR: NEXTAUTH_SECRET too short (minimum 32 characters required)"
        errors=$((errors + 1))
    else
        echo "✅ NEXTAUTH_SECRET configured securely"
    fi
    
    # Validate production settings
    if [ "$DEV_MODE" == "true" ]; then
        echo "⚠️  WARNING: DEV_MODE is enabled in production deployment"
        echo "   Set DEV_MODE=false for production security"
    else
        echo "✅ DEV_MODE disabled for production"
    fi
    
    if [ "$DEBUG" == "true" ]; then
        echo "⚠️  WARNING: DEBUG mode is enabled in production deployment"
        echo "   Set DEBUG=false for production security"
    else
        echo "✅ DEBUG mode disabled for production"
    fi
    
    # Check TLS configuration
    if [ "$TLS_ENABLED" != "true" ]; then
        echo "❌ ERROR: TLS_ENABLED must be true for production"
        errors=$((errors + 1))
    else
        echo "✅ TLS enabled for production"
    fi
    
    if [ $errors -gt 0 ]; then
        echo ""
        echo "❌ Security validation failed with $errors error(s)"
        echo "Please fix the above issues before deploying to production"
        exit 1
    fi
    
    echo "✅ Security configuration validation passed"
    echo ""
}

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

# Security defaults for production
DEV_MODE=${DEV_MODE:-"false"}
DEBUG=${DEBUG:-"false"}
TLS_ENABLED=${TLS_ENABLED:-"true"}
TOKEN_EXPIRE_HOURS=${TOKEN_EXPIRE_HOURS:-"8"}
RATE_LIMIT_ENABLED=${RATE_LIMIT_ENABLED:-"true"}
ENABLE_SECURITY_HEADERS=${ENABLE_SECURITY_HEADERS:-"true"}
CSP_ENABLED=${CSP_ENABLED:-"true"}

# Validate required variables
if [ -z "$PROJECT_ID" ] || [ -z "$DOMAIN" ]; then
    echo "Error: PROJECT_ID and DOMAIN are required. Set them in .env or pass as arguments."
    echo "Usage: $0 [PROJECT_ID] [CLUSTER_NAME] [DOMAIN] [REGION] [ZONE] [TAG] [SKIP_BUILD]"
    exit 1
fi

# Run security validation
validate_security_config

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
echo "Security Mode:   Production (DEV_MODE=$DEV_MODE, DEBUG=$DEBUG)"
echo "TLS Enabled:     $TLS_ENABLED"
echo "Token Expiry:    $TOKEN_EXPIRE_HOURS hours"
echo "--------------------------------------------------"

# Ensure we have cluster access (using the same zone as setup-cluster.sh)
gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE --project=$PROJECT_ID

# --- Workload Identity Setup ---
echo "🔑 Setting up Workload Identity bindings..."

# Define service account names, ensuring they match setup-cluster.sh
GSA_NAME="${CLUSTER_NAME}-workload-sa"
GSA_EMAIL="${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KSA_NAME="${CLUSTER_NAME}-sa"
USER_KSA_NAME="cmbcluster-user-sa"

# Allow the Kubernetes Service Account to impersonate the Google Service Account.
# This is the core of Workload Identity. It grants the KSA the 'workloadIdentityUser' role on the GSA.
echo "Binding backend KSA '$KSA_NAME' to GSA '$GSA_EMAIL'..."
gcloud iam service-accounts add-iam-policy-binding $GSA_EMAIL \
    --role="roles/iam.workloadIdentityUser" \
    --member="serviceAccount:${PROJECT_ID}.svc.id.goog[${K8S_NAMESPACE}/${KSA_NAME}]" \
    --project=$PROJECT_ID \
    --quiet || echo "✅ Backend IAM policy binding already exists."

# Also bind user environment service account to the same Google Service Account
echo "Binding user environment KSA '$USER_KSA_NAME' to GSA '$GSA_EMAIL'..."
gcloud iam service-accounts add-iam-policy-binding $GSA_EMAIL \
    --role="roles/iam.workloadIdentityUser" \
    --member="serviceAccount:${PROJECT_ID}.svc.id.goog[${K8S_NAMESPACE}/${USER_KSA_NAME}]" \
    --project=$PROJECT_ID \
    --quiet || echo "✅ User environment IAM policy binding already exists."

# Conditionally build images
if [ "$SKIP_BUILD" != "true" ]; then
    echo "🏗️ Building images..."
    
    # Force clean build if requested
    if [ "$FORCE_REBUILD" = "true" ]; then
        echo "🧹 Force cleaning previous builds..."
        rm -rf ./nextjs-frontend/.next
        rm -rf ./nextjs-frontend/out
        docker system prune -f || true
        
        echo "🏗️ Rebuilding NextJS frontend..."
        cd nextjs-frontend
        npm run build
        cd ..
    fi
    
    ./scripts/build-images.sh $PROJECT_ID $TAG $IMAGE_REPO
else
    echo "⏭️ Skipping image build..."
fi

# Create namespace
kubectl create namespace $K8S_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create secrets
echo "🔐 Creating enhanced security secrets..."

# Generate secure encryption key if not provided
if [ -z "$FILE_ENCRYPTION_KEY" ]; then
    echo "📝 Generating encryption key for environment files..."
    FILE_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || openssl rand -base64 32)
    echo "✅ Generated FILE_ENCRYPTION_KEY (store this securely for future deployments)"
fi

# Generate secure secret key if not provided
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" == "dev-secret-key-change-in-production" ]; then
    echo "📝 Generating secure SECRET_KEY for JWT tokens..."
    SECRET_KEY=$(openssl rand -hex 32)
    echo "✅ Generated SECRET_KEY (store this securely for future deployments)"
fi

# Generate secure NextAuth secret if not provided
if [ -z "$NEXTAUTH_SECRET" ] || [ "$NEXTAUTH_SECRET" == "your-secret-key-here-replace-in-production" ]; then
    echo "📝 Generating secure NEXTAUTH_SECRET for session management..."
    NEXTAUTH_SECRET=$(openssl rand -base64 32)
    echo "✅ Generated NEXTAUTH_SECRET (store this securely for future deployments)"
fi

# Create comprehensive backend secrets
kubectl create secret generic cmbcluster-backend-secrets \
    --from-literal=GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID}" \
    --from-literal=GOOGLE_CLIENT_SECRET="${GOOGLE_CLIENT_SECRET}" \
    --from-literal=SECRET_KEY="${SECRET_KEY}" \
    --from-literal=FILE_ENCRYPTION_KEY="${FILE_ENCRYPTION_KEY}" \
    --from-literal=DEV_MODE="${DEV_MODE}" \
    --from-literal=DEBUG="${DEBUG}" \
    --from-literal=TLS_ENABLED="${TLS_ENABLED}" \
    --from-literal=RATE_LIMIT_ENABLED="${RATE_LIMIT_ENABLED}" \
    --from-literal=ENABLE_SECURITY_HEADERS="${ENABLE_SECURITY_HEADERS}" \
    --from-literal=CSP_ENABLED="${CSP_ENABLED}" \
    --from-literal=API_URL="${API_URL}" \
    --from-literal=FRONTEND_URL="${FRONTEND_URL}" \
    --from-literal=JWT_ALGORITHM="${JWT_ALGORITHM}" \
    --from-literal=TOKEN_EXPIRE_HOURS="${TOKEN_EXPIRE_HOURS}" \
    --namespace=$K8S_NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

# Create frontend secrets for NextAuth
kubectl create secret generic cmbcluster-frontend-secrets \
    --from-literal=NEXTAUTH_SECRET="${NEXTAUTH_SECRET}" \
    --from-literal=GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID}" \
    --from-literal=GOOGLE_CLIENT_SECRET="${GOOGLE_CLIENT_SECRET}" \
    --from-literal=NEXTAUTH_URL="https://${DOMAIN}" \
    --from-literal=NEXT_PUBLIC_API_URL="https://api.${DOMAIN}" \
    --namespace=$K8S_NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Security secrets created successfully"

# Deploy using Helm with enhanced security configuration
echo "⚙️ Deploying with Helm and enhanced security settings..."
# Pass configuration from .env and other scripts to the Helm chart.
# This ensures the backend gets all required environment variables and prevents Pydantic validation errors.
helm upgrade --install cmbcluster  ./helm \
    --namespace $K8S_NAMESPACE \
    --wait \
    --timeout=10m \
    --disable-openapi-validation \
    --set global.projectId=$PROJECT_ID \
    --set global.clusterName=$CLUSTER_NAME \
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
    --set frontend.secretName=cmbcluster-frontend-secrets \
    --set-string backend.config.tokenExpireHours="$TOKEN_EXPIRE_HOURS" \
    --set-string backend.config.maxInactiveHours="$MAX_INACTIVE_HOURS" \
    --set-string backend.config.maxUserPods="$MAX_USER_PODS" \
    --set-string backend.config.devMode="$DEV_MODE" \
    --set-string backend.config.debug="$DEBUG" \
    --set-string backend.config.tlsEnabled="$TLS_ENABLED" \
    --set-string backend.config.rateLimitEnabled="$RATE_LIMIT_ENABLED" \
    --set-string backend.config.enableSecurityHeaders="$ENABLE_SECURITY_HEADERS" \
    --set-string backend.config.cspEnabled="$CSP_ENABLED" \
    --set-string frontend.config.nextAuthUrl="https://${DOMAIN}" \
    --set-string frontend.config.apiUrl="https://api.${DOMAIN}" \
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
  current_ip=$(gcloud dns record-sets list --zone="$dns_zone_name" --name="$domain_name." --type=A --format="value(rrdatas[0])" --project="$PROJECT_ID")

  if [[ "$current_ip" == "$ip_address" ]]; then
    echo "DNS record is already up to date. No changes needed."
    return 0
  fi

  # Use a transaction to make the change atomic and safe.
  gcloud dns record-sets transaction start --zone="$dns_zone_name" --project="$PROJECT_ID"

  # If a record already exists, remove the old one from the transaction.
  if [[ -n "$current_ip" ]]; then
    echo "Removing old A record pointing to $current_ip..."
    local current_ttl
    current_ttl=$(gcloud dns record-sets list --zone="$dns_zone_name" --name="$domain_name." --type=A --format="value(ttl)" --project="$PROJECT_ID")
    gcloud dns record-sets transaction remove --zone="$dns_zone_name" \
      --name="$domain_name." \
      --ttl="$current_ttl" \
      --type=A "$current_ip" \
      --project="$PROJECT_ID"
  fi

  # Add the new record to the transaction.
  echo "Adding new A record pointing to $ip_address..."
  gcloud dns record-sets transaction add --zone="$dns_zone_name" \
    --name="$domain_name." \
    --ttl=300 \
    --type=A "$ip_address" \
    --project="$PROJECT_ID"

  # Execute the transaction to apply the changes.
  echo "Executing DNS transaction..."
  if gcloud dns record-sets transaction execute --zone="$dns_zone_name" --project="$PROJECT_ID"; then
    echo "Successfully updated DNS record for $domain_name."
  else
    echo "Error: Failed to update DNS record. Aborting transaction." >&2
    gcloud dns record-sets transaction abort --zone="$dns_zone_name" --project="$PROJECT_ID"
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

# 3. Update the DNS record (skip for nip.io domains as they auto-resolve).
if [[ "$DOMAIN" == *".nip.io"* ]]; then
  echo "📝 Skipping DNS update for nip.io domain (auto-resolves to $INGRESS_IP)"
  echo "✅ Your domain $DOMAIN will automatically resolve to $INGRESS_IP"
else
  update_dns_record "$INGRESS_IP" "$DOMAIN"
  if [[ $? -ne 0 ]]; then
    echo "DNS update failed. Please check permissions and configuration." >&2
    exit 1
  fi
  echo "DNS automation complete."
fi
echo "✅ CMBCluster deployed successfully with enhanced security!"
echo ""
echo "🔒 Security Configuration:"
echo "- JWT Token Expiry: $TOKEN_EXPIRE_HOURS hours"
echo "- Rate Limiting: $RATE_LIMIT_ENABLED"
echo "- Security Headers: $ENABLE_SECURITY_HEADERS"
echo "- Content Security Policy: $CSP_ENABLED"
echo "- TLS/HTTPS: $TLS_ENABLED"
echo "- Development Mode: $DEV_MODE"
echo "- Debug Mode: $DEBUG"
echo ""
echo "🌐 Access your deployment:"
echo "Frontend: https://$DOMAIN"
echo "API: https://api.$DOMAIN"
echo "Docs: https://api.$DOMAIN/docs (disabled in production)"
echo ""
echo "� Security Verification:"
echo "1. Test authentication: https://$DOMAIN/auth/signin"
echo "2. Verify security headers: curl -I https://$DOMAIN"
echo "3. Check API authentication: curl -H 'Authorization: Bearer TOKEN' https://api.$DOMAIN/health"
echo ""
echo "�📋 Useful commands:"
echo "kubectl get pods -n cmbcluster"
echo "kubectl logs -f deployment/cmbcluster-backend -n cmbcluster"
echo "kubectl logs -f deployment/cmbcluster-frontend -n cmbcluster"
echo "kubectl get secrets -n cmbcluster"
echo ""
echo "🔍 Get ingress IP:"
echo "kubectl get ingress -n cmbcluster"
echo ""
echo "⚠️  Important Security Notes:"
echo "- Store generated secrets securely (SECRET_KEY, NEXTAUTH_SECRET, FILE_ENCRYPTION_KEY)"
echo "- Monitor authentication logs for suspicious activity"
echo "- Regularly update dependencies for security patches"
echo "- Review and rotate secrets periodically"
echo "- Configure monitoring and alerting for security events"
