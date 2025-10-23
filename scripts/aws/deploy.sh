#!/bin/bash
set -e

# ============================================================================
# AWS EKS Deployment Script for CMBCluster
# ============================================================================
#
# This script deploys CMBCluster to Amazon EKS using Helm with comprehensive
# security validation and configuration management.
#
# Prerequisites:
#   - AWS CLI v2 configured
#   - kubectl installed
#   - helm installed
#   - EKS cluster created (via setup-cluster.sh)
#   - Images pushed to ECR (via build-images.sh)
#   - S3 CSI driver installed on cluster
#   - AWS Load Balancer Controller installed
#   - cert-manager installed (optional, for TLS)
#
# Usage:
#   ./scripts/aws/deploy.sh [OPTIONS]
#
# Examples:
#   ./scripts/aws/deploy.sh
#   ./scripts/aws/deploy.sh --force-rebuild
#   ./scripts/aws/deploy.sh --skip-build
#
# ============================================================================

# Parse command line arguments
FORCE_REBUILD=false
SKIP_BUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force-rebuild|-f)
            FORCE_REBUILD=true
            echo "🔄 Force rebuild mode enabled"
            shift
            ;;
        --skip-build|-s)
            SKIP_BUILD=true
            echo "⏭️  Skip build mode enabled"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--force-rebuild|-f] [--skip-build|-s]"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# --- Security Configuration Validation ---
echo "🔒 Validating security configuration for production deployment..."

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

    # Check authentication provider configuration
    if [ "$AUTH_PROVIDER" == "google" ] || [ -z "$AUTH_PROVIDER" ] || [ "$AUTH_PROVIDER" == "auto" ]; then
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
    fi

    if [ "$AUTH_PROVIDER" == "cognito" ] || [ "$AUTH_PROVIDER" == "auto" ]; then
        if [ -z "$COGNITO_USER_POOL_ID" ]; then
            echo "⚠️  WARNING: COGNITO_USER_POOL_ID not configured"
            echo "   Run ./scripts/aws/setup-cognito.sh to create Cognito User Pool"
        fi

        if [ -z "$COGNITO_CLIENT_ID" ]; then
            echo "⚠️  WARNING: COGNITO_CLIENT_ID not configured"
        fi
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
# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Load .env file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "📝 Loading environment variables from .env file..."
    set -o allexport
    source "$PROJECT_ROOT/.env"
    set +o allexport
else
    log_error ".env file not found at $PROJECT_ROOT/.env"
    exit 1
fi

# Configuration with defaults
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID}"
EKS_CLUSTER_NAME="${EKS_CLUSTER_NAME:-cmbcluster-eks}"
NAMESPACE="${NAMESPACE:-cmbcluster}"
DOMAIN="${DOMAIN:-cmbcluster.example.com}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
CLOUD_PROVIDER="${CLOUD_PROVIDER:-aws}"
AUTH_PROVIDER="${AUTH_PROVIDER:-auto}"

# Security defaults for production
DEV_MODE="${DEV_MODE:-false}"
DEBUG="${DEBUG:-false}"
TLS_ENABLED="${TLS_ENABLED:-true}"
TOKEN_EXPIRE_HOURS="${TOKEN_EXPIRE_HOURS:-8}"
RATE_LIMIT_ENABLED="${RATE_LIMIT_ENABLED:-true}"
ENABLE_SECURITY_HEADERS="${ENABLE_SECURITY_HEADERS:-true}"
CSP_ENABLED="${CSP_ENABLED:-true}"

# Validate required variables
if [ -z "$AWS_ACCOUNT_ID" ]; then
    log_error "AWS_ACCOUNT_ID is not set in .env"
    exit 1
fi

if [ -z "$DOMAIN" ]; then
    log_error "DOMAIN is not set in .env"
    exit 1
fi

# Run security validation
validate_security_config

# ECR registry URL
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# IRSA role ARN (should be created by setup-cluster.sh)
IRSA_ROLE_ARN="${IRSA_ROLE_ARN:-arn:aws:iam::${AWS_ACCOUNT_ID}:role/${EKS_CLUSTER_NAME}-workload-role}"

# S3 bucket names
S3_DATABASE_BUCKET="${S3_DATABASE_BUCKET:-${EKS_CLUSTER_NAME}-db-${AWS_ACCOUNT_ID}}"
S3_USER_BUCKET_PREFIX="${S3_USER_BUCKET_PREFIX:-${EKS_CLUSTER_NAME}-user}"

# API URLs
API_URL="${API_URL:-https://api.${DOMAIN}}"
FRONTEND_URL="${FRONTEND_URL:-https://${DOMAIN}}"

log_info "🚀 Deploying CMBCluster with the following configuration:"
log_info "--------------------------------------------------"
log_info "Cloud Provider:  $CLOUD_PROVIDER"
log_info "AWS Region:      $AWS_REGION"
log_info "AWS Account ID:  $AWS_ACCOUNT_ID"
log_info "EKS Cluster:     $EKS_CLUSTER_NAME"
log_info "Namespace:       $NAMESPACE"
log_info "Domain:          $DOMAIN"
log_info "ECR Registry:    $ECR_REGISTRY"
log_info "Image Tag:       $IMAGE_TAG"
log_info "Auth Provider:   $AUTH_PROVIDER"
log_info "Security Mode:   Production (DEV_MODE=$DEV_MODE, DEBUG=$DEBUG)"
log_info "TLS Enabled:     $TLS_ENABLED"
log_info "Token Expiry:    $TOKEN_EXPIRE_HOURS hours"
log_info "IRSA Role:       $IRSA_ROLE_ARN"
log_info "DB Bucket:       $S3_DATABASE_BUCKET"
log_info "--------------------------------------------------"

# Update kubeconfig for EKS
log_info "🔑 Updating kubeconfig for EKS cluster..."
aws eks update-kubeconfig --name "$EKS_CLUSTER_NAME" --region "$AWS_REGION"

if [ $? -eq 0 ]; then
    log_success "Kubeconfig updated"
else
    log_error "Failed to update kubeconfig"
    exit 1
fi

# Conditionally build images
if [ "$SKIP_BUILD" != "true" ]; then
    echo "🏗️ Building images..."

    # Force clean build if requested
    if [ "$FORCE_REBUILD" = "true" ]; then
        echo "🧹 Force cleaning previous builds..."
        rm -rf "$PROJECT_ROOT/nextjs-frontend/.next"
        rm -rf "$PROJECT_ROOT/nextjs-frontend/out"
        docker system prune -f || true

        echo "🏗️ Rebuilding NextJS frontend..."
        cd "$PROJECT_ROOT/nextjs-frontend"
        npm run build
        cd "$PROJECT_ROOT"
    fi

    "$SCRIPT_DIR/build-images.sh" "$IMAGE_TAG"
else
    echo "⏭️ Skipping image build..."
fi

# Create namespace
log_info "📦 Creating namespace: $NAMESPACE..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
log_success "Namespace ready"

# Generate secrets
log_info "🔐 Creating enhanced security secrets..."

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

# Create comprehensive backend secrets (deployment-agnostic)
kubectl create secret generic cmbcluster-backend-secrets \
    --from-literal=SECRET_KEY="${SECRET_KEY}" \
    --from-literal=FILE_ENCRYPTION_KEY="${FILE_ENCRYPTION_KEY}" \
    --from-literal=GOOGLE_CLIENT_SECRET="${GOOGLE_CLIENT_SECRET:-}" \
    --from-literal=COGNITO_CLIENT_SECRET="${COGNITO_CLIENT_SECRET:-}" \
    --from-literal=DEV_MODE="${DEV_MODE}" \
    --from-literal=DEBUG="${DEBUG}" \
    --from-literal=TLS_ENABLED="${TLS_ENABLED}" \
    --from-literal=RATE_LIMIT_ENABLED="${RATE_LIMIT_ENABLED}" \
    --from-literal=ENABLE_SECURITY_HEADERS="${ENABLE_SECURITY_HEADERS}" \
    --from-literal=CSP_ENABLED="${CSP_ENABLED}" \
    --from-literal=JWT_ALGORITHM="${JWT_ALGORITHM:-HS256}" \
    --from-literal=TOKEN_EXPIRE_HOURS="${TOKEN_EXPIRE_HOURS}" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

log_success "Backend secrets created"

# Create frontend secrets for NextAuth (deployment-agnostic)
kubectl create secret generic cmbcluster-frontend-secrets \
    --from-literal=NEXTAUTH_SECRET="${NEXTAUTH_SECRET}" \
    --from-literal=GOOGLE_CLIENT_SECRET="${GOOGLE_CLIENT_SECRET:-}" \
    --from-literal=COGNITO_CLIENT_SECRET="${COGNITO_CLIENT_SECRET:-}" \
    --from-literal=NEXTAUTH_URL="${FRONTEND_URL}" \
    --from-literal=NEXT_PUBLIC_API_URL="${API_URL}" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

log_success "Frontend secrets created"

# Deploy using Helm with enhanced security configuration
log_info "⚙️ Deploying with Helm and enhanced security settings..."

helm upgrade --install cmbcluster "$PROJECT_ROOT/helm" \
    --namespace "$NAMESPACE" \
    --wait \
    --timeout=10m \
    --disable-openapi-validation \
    --set global.cloudProvider="$CLOUD_PROVIDER" \
    --set global.clusterName="$EKS_CLUSTER_NAME" \
    --set global.registryUrl="$ECR_REGISTRY" \
    --set global.imageTag="$IMAGE_TAG" \
    --set global.aws.accountId="$AWS_ACCOUNT_ID" \
    --set global.aws.region="$AWS_REGION" \
    --set global.aws.roleArn="$IRSA_ROLE_ARN" \
    --set ingress.baseDomain="$DOMAIN" \
    --set ingress.enabled=true \
    --set ingress.className="alb" \
    --set ingress.tls.enabled="$TLS_ENABLED" \
    --set backend.image.repository="$ECR_REGISTRY/${EKS_CLUSTER_NAME}-backend" \
    --set backend.image.tag="$IMAGE_TAG" \
    --set backend.config.cloudProvider="$CLOUD_PROVIDER" \
    --set backend.config.authProvider="$AUTH_PROVIDER" \
    --set backend.config.googleClientId="${GOOGLE_CLIENT_ID:-}" \
    --set backend.config.cognitoUserPoolId="${COGNITO_USER_POOL_ID:-}" \
    --set backend.config.cognitoClientId="${COGNITO_CLIENT_ID:-}" \
    --set backend.config.cognitoIssuer="${COGNITO_ISSUER:-}" \
    --set-string backend.config.tokenExpireHours="$TOKEN_EXPIRE_HOURS" \
    --set frontend.image.repository="$ECR_REGISTRY/${EKS_CLUSTER_NAME}-frontend" \
    --set frontend.image.tag="$IMAGE_TAG" \
    --set frontend.config.authProvider="$AUTH_PROVIDER" \
    --set frontend.config.googleClientId="${GOOGLE_CLIENT_ID:-}" \
    --set frontend.config.cognitoClientId="${COGNITO_CLIENT_ID:-}" \
    --set frontend.config.cognitoIssuer="${COGNITO_ISSUER:-}" \
    --set userEnvironment.image.repository="$ECR_REGISTRY/${EKS_CLUSTER_NAME}-user-env" \
    --set userEnvironment.image.tag="$IMAGE_TAG" \
    --set storage.aws.databaseBucketName="$S3_DATABASE_BUCKET" \
    --set backend.secretName=cmbcluster-backend-secrets \
    --set frontend.secretName=cmbcluster-frontend-secrets

if [ $? -eq 0 ]; then
    log_success "Helm deployment successful"
else
    log_error "Helm deployment failed"
    exit 1
fi

# Get deployment status
log_info ""
log_info "📊 Checking deployment status..."
kubectl get pods -n "$NAMESPACE"

# Get ingress information
log_info ""
log_info "🌐 Ingress information:"
kubectl get ingress -n "$NAMESPACE"

# Get load balancer DNS
LOAD_BALANCER_DNS=$(kubectl get ingress -n "$NAMESPACE" -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Not available yet")

log_info ""
log_info "==================================="
log_info "✅ Deployment Complete"
log_info "==================================="
log_success "Namespace:           $NAMESPACE"
log_success "Domain:              $DOMAIN"
log_success "Load Balancer DNS:   $LOAD_BALANCER_DNS"
log_success "Auth Provider:       $AUTH_PROVIDER"
log_success "Cloud Provider:      $CLOUD_PROVIDER"
log_info "==================================="
log_info ""
log_info "📋 Next Steps:"
log_info "1. Update DNS records to point $DOMAIN to the Load Balancer:"
log_info "   - Create A/CNAME record for $DOMAIN → $LOAD_BALANCER_DNS"
log_info "   - Create A/CNAME record for api.$DOMAIN → $LOAD_BALANCER_DNS"
log_info "   - Create A/CNAME record for *.$DOMAIN → $LOAD_BALANCER_DNS (for user envs)"
log_info ""
log_info "2. Wait for TLS certificates to be issued (if using cert-manager)"
log_info ""
log_info "3. Access the application:"
log_info "   - Frontend: $FRONTEND_URL"
log_info "   - API:      $API_URL"
log_info ""
log_info "4. Monitor deployment:"
log_info "   - Pods:     kubectl get pods -n $NAMESPACE"
log_info "   - Logs:     kubectl logs -n $NAMESPACE -l app.kubernetes.io/component=backend -f"
log_info "   - Events:   kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'"
log_info ""

log_success "🎉 Deployment completed successfully!"
