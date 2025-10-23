#!/bin/bash

# CMBCluster Configuration Validator
# Validates environment configuration before deployment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0

# Functions
error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    ((ERRORS++))
}

warn() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    ((WARNINGS++))
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

info() {
    echo -e "$1"
}

# Main validation function
validate_config() {
    local cloud_provider=${1:-}

    echo "=== CMBCluster Configuration Validator ==="
    echo ""

    # Check .env file exists
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        error ".env file not found in project root"
        echo "Run: cp .env.example .env"
        exit 1
    fi

    # Load environment variables
    set -a
    source "$PROJECT_ROOT/.env"
    set +a

    # Override cloud provider if specified
    if [ -n "$cloud_provider" ]; then
        CLOUD_PROVIDER=$cloud_provider
    fi

    echo "Target Cloud Provider: ${CLOUD_PROVIDER:-not set}"
    echo ""

    # Validate core settings
    validate_core_settings

    # Validate cloud-specific settings
    case "${CLOUD_PROVIDER:-}" in
        gcp)
            validate_gcp_settings
            ;;
        aws)
            validate_aws_settings
            ;;
        *)
            error "CLOUD_PROVIDER must be 'gcp' or 'aws', got: '${CLOUD_PROVIDER:-}'"
            ;;
    esac

    # Validate authentication settings
    validate_auth_settings

    # Validate security settings
    validate_security_settings

    # Validate networking settings
    validate_networking_settings

    # Print summary
    print_summary
}

validate_core_settings() {
    info "[Core Settings]"

    if [ -z "${CLOUD_PROVIDER:-}" ]; then
        error "CLOUD_PROVIDER not set"
    else
        success "CLOUD_PROVIDER: $CLOUD_PROVIDER"
    fi

    if [ -z "${NAMESPACE:-}" ]; then
        warn "NAMESPACE not set, will use default: cmbcluster"
    else
        success "NAMESPACE: $NAMESPACE"
    fi

    echo ""
}

validate_gcp_settings() {
    info "[GCP Settings]"

    if [ -z "${PROJECT_ID:-}" ]; then
        error "PROJECT_ID not set (required for GCP)"
    elif [ "$PROJECT_ID" = "cmbcluster" ]; then
        warn "PROJECT_ID is set to default value 'cmbcluster'"
    else
        success "PROJECT_ID: $PROJECT_ID"
    fi

    if [ -z "${CLUSTER_NAME:-}" ]; then
        error "CLUSTER_NAME not set (required for GCP)"
    else
        success "CLUSTER_NAME: $CLUSTER_NAME"
    fi

    if [ -z "${REGION:-}" ]; then
        warn "REGION not set, will use default: us-central1"
    else
        success "REGION: $REGION"
    fi

    if [ -z "${ZONE:-}" ]; then
        warn "ZONE not set, will use default: us-central1-a"
    else
        success "ZONE: $ZONE"
    fi

    echo ""
}

validate_aws_settings() {
    info "[AWS Settings]"

    if [ -z "${AWS_ACCOUNT_ID:-}" ]; then
        error "AWS_ACCOUNT_ID not set (required for AWS)"
    elif ! [[ "${AWS_ACCOUNT_ID}" =~ ^[0-9]{12}$ ]]; then
        error "AWS_ACCOUNT_ID must be 12 digits, got: ${AWS_ACCOUNT_ID}"
    else
        success "AWS_ACCOUNT_ID: $AWS_ACCOUNT_ID"
    fi

    if [ -z "${AWS_REGION:-}" ]; then
        error "AWS_REGION not set (required for AWS)"
    else
        success "AWS_REGION: $AWS_REGION"
    fi

    if [ -z "${EKS_CLUSTER_NAME:-}" ]; then
        error "EKS_CLUSTER_NAME not set (required for AWS)"
    else
        success "EKS_CLUSTER_NAME: $EKS_CLUSTER_NAME"
    fi

    if [ -z "${ECR_REGISTRY_URL:-}" ]; then
        warn "ECR_REGISTRY_URL not set, will be auto-generated"
    else
        success "ECR_REGISTRY_URL: $ECR_REGISTRY_URL"
    fi

    echo ""
}

validate_auth_settings() {
    info "[Authentication Settings]"

    local has_google=false
    local has_cognito=false

    # Check Google OAuth
    if [ -n "${GOOGLE_CLIENT_ID:-}" ] && [ -n "${GOOGLE_CLIENT_SECRET:-}" ]; then
        success "Google OAuth configured"
        has_google=true
    fi

    # Check AWS Cognito
    if [ -n "${COGNITO_USER_POOL_ID:-}" ] && \
       [ -n "${COGNITO_CLIENT_ID:-}" ] && \
       [ -n "${COGNITO_CLIENT_SECRET:-}" ] && \
       [ -n "${COGNITO_ISSUER:-}" ]; then
        success "AWS Cognito configured"
        has_cognito=true
    fi

    # Validate at least one provider is configured
    if [ "$has_google" = false ] && [ "$has_cognito" = false ]; then
        error "No authentication provider configured (need Google OAuth or AWS Cognito)"
    fi

    # Validate AUTH_PROVIDER setting
    if [ -n "${AUTH_PROVIDER:-}" ]; then
        case "${AUTH_PROVIDER}" in
            auto)
                success "AUTH_PROVIDER: auto (will auto-detect)"
                ;;
            google)
                if [ "$has_google" = false ]; then
                    error "AUTH_PROVIDER=google but Google OAuth credentials not configured"
                else
                    success "AUTH_PROVIDER: google (explicit)"
                fi
                ;;
            cognito)
                if [ "$has_cognito" = false ]; then
                    error "AUTH_PROVIDER=cognito but Cognito credentials not configured"
                else
                    success "AUTH_PROVIDER: cognito (explicit)"
                fi
                ;;
            *)
                error "AUTH_PROVIDER must be 'auto', 'google', or 'cognito', got: '${AUTH_PROVIDER}'"
                ;;
        esac
    else
        warn "AUTH_PROVIDER not set, will default to 'auto'"
    fi

    echo ""
}

validate_security_settings() {
    info "[Security Settings]"

    # Secret key validation
    if [ -z "${SECRET_KEY:-}" ]; then
        error "SECRET_KEY not set (required for production)"
    elif [ "${SECRET_KEY}" = "dev-secret-key-change-in-production" ]; then
        error "SECRET_KEY is still set to default development value"
    elif [ ${#SECRET_KEY} -lt 32 ]; then
        warn "SECRET_KEY is only ${#SECRET_KEY} characters (minimum 32 recommended)"
    else
        success "SECRET_KEY set (${#SECRET_KEY} characters)"
    fi

    # NextAuth secret validation
    if [ -z "${NEXTAUTH_SECRET:-}" ]; then
        error "NEXTAUTH_SECRET not set (required for NextAuth)"
    else
        success "NEXTAUTH_SECRET set"
    fi

    # File encryption key validation
    if [ -z "${FILE_ENCRYPTION_KEY:-}" ]; then
        warn "FILE_ENCRYPTION_KEY not set (optional but recommended)"
    else
        success "FILE_ENCRYPTION_KEY set"
    fi

    # Development mode check
    if [ "${DEV_MODE:-false}" = "true" ]; then
        warn "DEV_MODE is enabled (should be false for production)"
    else
        success "DEV_MODE: false (production mode)"
    fi

    # Debug mode check
    if [ "${DEBUG:-false}" = "true" ]; then
        warn "DEBUG is enabled (should be false for production)"
    else
        success "DEBUG: false"
    fi

    # TLS check
    if [ "${TLS_ENABLED:-true}" != "true" ]; then
        error "TLS_ENABLED is not true (required for production)"
    else
        success "TLS_ENABLED: true"
    fi

    echo ""
}

validate_networking_settings() {
    info "[Networking Settings]"

    # Domain validation
    if [ -z "${DOMAIN:-}" ]; then
        error "DOMAIN not set (required)"
    elif [[ "${DOMAIN}" == *".nip.io" ]]; then
        warn "Using nip.io domain (only for testing, not production)"
        success "DOMAIN: $DOMAIN (nip.io - testing)"
    else
        success "DOMAIN: $DOMAIN"
    fi

    # API URL validation
    if [ -z "${API_URL:-}" ]; then
        error "API_URL not set (required)"
    elif [[ ! "${API_URL}" =~ ^https:// ]]; then
        warn "API_URL does not start with https:// (insecure)"
    else
        success "API_URL: $API_URL"
    fi

    # Frontend URL validation
    if [ -z "${FRONTEND_URL:-}" ]; then
        error "FRONTEND_URL not set (required)"
    elif [[ ! "${FRONTEND_URL}" =~ ^https:// ]]; then
        warn "FRONTEND_URL does not start with https:// (insecure)"
    else
        success "FRONTEND_URL: $FRONTEND_URL"
    fi

    # Let's Encrypt email validation
    if [ -z "${LETSENCRYPT_EMAIL:-}" ]; then
        error "LETSENCRYPT_EMAIL not set (required for TLS certificates)"
    elif [[ ! "${LETSENCRYPT_EMAIL}" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        error "LETSENCRYPT_EMAIL is not a valid email address: ${LETSENCRYPT_EMAIL}"
    else
        success "LETSENCRYPT_EMAIL: $LETSENCRYPT_EMAIL"
    fi

    echo ""
}

print_summary() {
    echo "=== Validation Summary ==="
    echo ""

    if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
        success "Configuration is valid! No errors or warnings."
        echo ""
        echo "✨ Ready to deploy!"
        exit 0
    elif [ $ERRORS -eq 0 ]; then
        warn "Found $WARNINGS warning(s) but no errors."
        echo ""
        echo "⚠️  Configuration is valid but has warnings. Review warnings before deploying to production."
        exit 0
    else
        error "Found $ERRORS error(s) and $WARNINGS warning(s)."
        echo ""
        echo "❌ Configuration is INVALID. Please fix errors before deploying."
        exit 1
    fi
}

# Help message
show_help() {
    cat << EOF
CMBCluster Configuration Validator

Usage: $0 [CLOUD_PROVIDER]

Arguments:
  CLOUD_PROVIDER    Optional. Force validation for specific cloud: 'gcp' or 'aws'
                    If not specified, uses CLOUD_PROVIDER from .env

Examples:
  $0              # Validate using CLOUD_PROVIDER from .env
  $0 gcp          # Validate GCP configuration
  $0 aws          # Validate AWS configuration

Exit codes:
  0 - Configuration valid
  1 - Configuration invalid (errors found)

EOF
}

# Main execution
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        validate_config "$@"
        ;;
esac
