#!/bin/bash

# ============================================================================
# AWS Cognito User Pool Setup Script for CMBCluster
# ============================================================================
#
# This script creates and configures an AWS Cognito User Pool for authentication.
#
# Prerequisites:
#   - AWS CLI v2 installed and configured
#   - Appropriate AWS permissions (Cognito, IAM)
#   - jq installed for JSON processing
#
# Usage:
#   ./scripts/aws/setup-cognito.sh [REGION] [POOL_NAME] [DOMAIN]
#
# Examples:
#   ./scripts/aws/setup-cognito.sh us-east-1 cmbcluster-users app.example.com
#   ./scripts/aws/setup-cognito.sh  # Uses values from .env
#
# ============================================================================

set -e  # Exit on error

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install AWS CLI v2."
        exit 1
    fi

    # Check jq
    if ! command -v jq &> /dev/null; then
        log_error "jq not found. Please install jq for JSON processing."
        exit 1
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Please run 'aws configure'."
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Load configuration from .env file
load_config() {
    if [ -f .env ]; then
        log_info "Loading configuration from .env file..."
        export $(grep -v '^#' .env | xargs)
    else
        log_warning ".env file not found, using command-line arguments or defaults"
    fi
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Load configuration
cd "$PROJECT_ROOT"
load_config

# Configuration with defaults
AWS_REGION="${1:-${AWS_REGION:-us-east-1}}"
USER_POOL_NAME="${2:-${COGNITO_USER_POOL_NAME:-cmbcluster-users}}"
APP_DOMAIN="${3:-${BASE_DOMAIN:-app.cmbcluster.local}}"
CLUSTER_NAME="${EKS_CLUSTER_NAME:-cmbcluster-eks}"

log_info "==================================="
log_info "AWS Cognito Setup Configuration"
log_info "==================================="
log_info "Region: $AWS_REGION"
log_info "User Pool Name: $USER_POOL_NAME"
log_info "App Domain: $APP_DOMAIN"
log_info "Cluster Name: $CLUSTER_NAME"
log_info "==================================="

# Check prerequisites
check_prerequisites

# Create User Pool
log_info "Creating Cognito User Pool: $USER_POOL_NAME..."

USER_POOL_ID=$(aws cognito-idp create-user-pool \
    --region "$AWS_REGION" \
    --pool-name "$USER_POOL_NAME" \
    --auto-verified-attributes email \
    --username-attributes email \
    --username-configuration CaseSensitive=false \
    --policies '{
        "PasswordPolicy": {
            "MinimumLength": 8,
            "RequireUppercase": true,
            "RequireLowercase": true,
            "RequireNumbers": true,
            "RequireSymbols": true,
            "TemporaryPasswordValidityDays": 7
        }
    }' \
    --schema '[
        {
            "Name": "email",
            "Required": true,
            "Mutable": true,
            "AttributeDataType": "String"
        },
        {
            "Name": "name",
            "Required": false,
            "Mutable": true,
            "AttributeDataType": "String"
        }
    ]' \
    --mfa-configuration OPTIONAL \
    --user-pool-tags "Project=CMBCluster,ManagedBy=Script,Cluster=$CLUSTER_NAME" \
    --account-recovery-setting '{
        "RecoveryMechanisms": [
            {
                "Priority": 1,
                "Name": "verified_email"
            }
        ]
    }' \
    --email-configuration EmailSendingAccount=COGNITO_DEFAULT \
    --admin-create-user-config '{
        "AllowAdminCreateUserOnly": false,
        "InviteMessageTemplate": {
            "EmailSubject": "Welcome to CMBCluster",
            "EmailMessage": "Welcome to CMBCluster! Your username is {username} and temporary password is {####}. Please sign in and change your password."
        }
    }' \
    --verification-message-template '{
        "DefaultEmailOption": "CONFIRM_WITH_CODE",
        "EmailSubject": "CMBCluster Email Verification",
        "EmailMessage": "Your verification code is {####}"
    }' \
    --query 'UserPool.Id' \
    --output text)

if [ -z "$USER_POOL_ID" ]; then
    log_error "Failed to create user pool"
    exit 1
fi

log_success "User pool created: $USER_POOL_ID"

# Generate callback URLs
CALLBACK_URLS="https://${APP_DOMAIN}/api/auth/callback/cognito,http://localhost:3000/api/auth/callback/cognito"
LOGOUT_URLS="https://${APP_DOMAIN},http://localhost:3000"

# Create App Client
log_info "Creating app client..."

APP_CLIENT_ID=$(aws cognito-idp create-user-pool-client \
    --region "$AWS_REGION" \
    --user-pool-id "$USER_POOL_ID" \
    --client-name "${USER_POOL_NAME}-web-client" \
    --generate-secret \
    --refresh-token-validity 30 \
    --access-token-validity 8 \
    --id-token-validity 8 \
    --token-validity-units '{
        "RefreshToken": "days",
        "AccessToken": "hours",
        "IdToken": "hours"
    }' \
    --read-attributes email email_verified name \
    --write-attributes email name \
    --explicit-auth-flows ALLOW_REFRESH_TOKEN_AUTH ALLOW_USER_SRP_AUTH ALLOW_USER_PASSWORD_AUTH \
    --supported-identity-providers COGNITO \
    --callback-urls "$CALLBACK_URLS" \
    --logout-urls "$LOGOUT_URLS" \
    --allowed-o-auth-flows authorization_code implicit \
    --allowed-o-auth-scopes openid email profile \
    --allowed-o-auth-flows-user-pool-client \
    --prevent-user-existence-errors ENABLED \
    --enable-token-revocation \
    --query 'UserPoolClient.ClientId' \
    --output text)

if [ -z "$APP_CLIENT_ID" ]; then
    log_error "Failed to create app client"
    exit 1
fi

log_success "App client created: $APP_CLIENT_ID"

# Get the client secret
log_info "Retrieving client secret..."

APP_CLIENT_SECRET=$(aws cognito-idp describe-user-pool-client \
    --region "$AWS_REGION" \
    --user-pool-id "$USER_POOL_ID" \
    --client-id "$APP_CLIENT_ID" \
    --query 'UserPoolClient.ClientSecret' \
    --output text)

if [ -z "$APP_CLIENT_SECRET" ]; then
    log_error "Failed to retrieve client secret"
    exit 1
fi

log_success "Client secret retrieved"

# Generate Cognito issuer URL
COGNITO_ISSUER="https://cognito-idp.${AWS_REGION}.amazonaws.com/${USER_POOL_ID}"

# Create Cognito domain (optional, for hosted UI)
log_info "Setting up Cognito domain..."

COGNITO_DOMAIN_PREFIX="${CLUSTER_NAME}-$(date +%s)"

aws cognito-idp create-user-pool-domain \
    --region "$AWS_REGION" \
    --domain "$COGNITO_DOMAIN_PREFIX" \
    --user-pool-id "$USER_POOL_ID" \
    > /dev/null 2>&1 || log_warning "Cognito domain may already exist or failed to create"

log_success "Cognito domain configured: ${COGNITO_DOMAIN_PREFIX}.auth.${AWS_REGION}.amazoncognito.com"

# Output configuration
log_info ""
log_info "==================================="
log_info "Cognito Configuration Complete"
log_info "==================================="
log_success "User Pool ID: $USER_POOL_ID"
log_success "App Client ID: $APP_CLIENT_ID"
log_success "Issuer: $COGNITO_ISSUER"
log_success "Domain: ${COGNITO_DOMAIN_PREFIX}.auth.${AWS_REGION}.amazoncognito.com"
log_info "==================================="

# Generate .env additions
log_info ""
log_info "Add the following to your .env file:"
log_info ""
echo "# AWS Cognito Configuration"
echo "COGNITO_USER_POOL_ID=$USER_POOL_ID"
echo "COGNITO_CLIENT_ID=$APP_CLIENT_ID"
echo "COGNITO_CLIENT_SECRET=$APP_CLIENT_SECRET"
echo "COGNITO_ISSUER=$COGNITO_ISSUER"
echo "COGNITO_DOMAIN=${COGNITO_DOMAIN_PREFIX}.auth.${AWS_REGION}.amazoncognito.com"
echo ""

# Save to a separate file for reference
OUTPUT_FILE="cognito-config-${USER_POOL_ID}.env"
cat > "$OUTPUT_FILE" << EOF
# AWS Cognito Configuration
# Generated: $(date)
COGNITO_USER_POOL_ID=$USER_POOL_ID
COGNITO_CLIENT_ID=$APP_CLIENT_ID
COGNITO_CLIENT_SECRET=$APP_CLIENT_SECRET
COGNITO_ISSUER=$COGNITO_ISSUER
COGNITO_DOMAIN=${COGNITO_DOMAIN_PREFIX}.auth.${AWS_REGION}.amazoncognito.com

# Callback URLs configured:
# - https://${APP_DOMAIN}/api/auth/callback/cognito
# - http://localhost:3000/api/auth/callback/cognito
EOF

log_success "Configuration saved to: $OUTPUT_FILE"

log_info ""
log_info "Next Steps:"
log_info "1. Add the Cognito configuration to your .env file"
log_info "2. Update CLOUD_PROVIDER to 'aws' in .env if needed"
log_info "3. Restart your backend and frontend services"
log_info "4. Test authentication at: https://${APP_DOMAIN}/auth/signin"
log_info ""

log_success "Cognito setup completed successfully!"
