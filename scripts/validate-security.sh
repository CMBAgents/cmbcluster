#!/bin/bash
# Security Validation Script for CMB Cluster
# Run this before production deployment to ensure security configuration is correct

set -e

echo "🔍 CMB Cluster Security Validation"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0
CHECKS=0

# Function to print status
print_status() {
    local status=$1
    local message=$2
    case $status in
        "PASS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "FAIL")
            echo -e "${RED}❌ $message${NC}"
            ERRORS=$((ERRORS + 1))
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  $message${NC}"
            WARNINGS=$((WARNINGS + 1))
            ;;
    esac
    CHECKS=$((CHECKS + 1))
}

# Load environment variables
if [ -f .env ]; then
    set -o allexport
    source .env
    set +o allexport
    print_status "PASS" "Environment file loaded"
else
    print_status "FAIL" "No .env file found - run ./scripts/setup-production-env.sh first"
    exit 1
fi

echo ""
echo "🔐 Security Configuration Validation"
echo "====================================="

# Check SECRET_KEY
if [ -z "$SECRET_KEY" ]; then
    print_status "FAIL" "SECRET_KEY not set"
elif [ "$SECRET_KEY" == "dev-secret-key-change-in-production" ]; then
    print_status "FAIL" "SECRET_KEY using development default"
elif [ ${#SECRET_KEY} -lt 32 ]; then
    print_status "FAIL" "SECRET_KEY too short (${#SECRET_KEY} chars, minimum 32)"
else
    print_status "PASS" "SECRET_KEY configured securely (${#SECRET_KEY} chars)"
fi

# Check NEXTAUTH_SECRET
if [ -z "$NEXTAUTH_SECRET" ]; then
    print_status "FAIL" "NEXTAUTH_SECRET not set"
elif [ "$NEXTAUTH_SECRET" == "your-secret-key-here-replace-in-production" ]; then
    print_status "FAIL" "NEXTAUTH_SECRET using development default"
elif [ ${#NEXTAUTH_SECRET} -lt 32 ]; then
    print_status "FAIL" "NEXTAUTH_SECRET too short (${#NEXTAUTH_SECRET} chars, minimum 32)"
else
    print_status "PASS" "NEXTAUTH_SECRET configured securely (${#NEXTAUTH_SECRET} chars)"
fi

# Check Google OAuth
if [ -z "$GOOGLE_CLIENT_ID" ]; then
    print_status "FAIL" "GOOGLE_CLIENT_ID not set"
elif [ "$GOOGLE_CLIENT_ID" == "your-google-oauth-client-id" ]; then
    print_status "FAIL" "GOOGLE_CLIENT_ID not configured (still using placeholder)"
else
    print_status "PASS" "GOOGLE_CLIENT_ID configured"
fi

if [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    print_status "FAIL" "GOOGLE_CLIENT_SECRET not set"
elif [ "$GOOGLE_CLIENT_SECRET" == "your-google-oauth-client-secret" ]; then
    print_status "FAIL" "GOOGLE_CLIENT_SECRET not configured (still using placeholder)"
else
    print_status "PASS" "GOOGLE_CLIENT_SECRET configured"
fi

# Check project configuration
if [ -z "$PROJECT_ID" ]; then
    print_status "FAIL" "PROJECT_ID not set"
elif [ "$PROJECT_ID" == "your-gcp-project-id" ]; then
    print_status "FAIL" "PROJECT_ID not configured (still using placeholder)"
else
    print_status "PASS" "PROJECT_ID configured: $PROJECT_ID"
fi

if [ -z "$DOMAIN" ]; then
    print_status "FAIL" "DOMAIN not set"
elif [ "$DOMAIN" == "yourdomain.com" ]; then
    print_status "FAIL" "DOMAIN not configured (still using placeholder)"
else
    print_status "PASS" "DOMAIN configured: $DOMAIN"
fi

# Check security settings
if [ "$DEV_MODE" == "true" ]; then
    print_status "WARN" "DEV_MODE is enabled in production"
else
    print_status "PASS" "DEV_MODE disabled for production"
fi

if [ "$DEBUG" == "true" ]; then
    print_status "WARN" "DEBUG mode enabled in production"
else
    print_status "PASS" "DEBUG mode disabled for production"
fi

if [ "$TLS_ENABLED" != "true" ]; then
    print_status "FAIL" "TLS_ENABLED must be true for production"
else
    print_status "PASS" "TLS enabled for production"
fi

# Check optional but recommended settings
if [ "$RATE_LIMIT_ENABLED" != "true" ]; then
    print_status "WARN" "Rate limiting not enabled"
else
    print_status "PASS" "Rate limiting enabled"
fi

if [ "$ENABLE_SECURITY_HEADERS" != "true" ]; then
    print_status "WARN" "Security headers not enabled"
else
    print_status "PASS" "Security headers enabled"
fi

if [ "$CSP_ENABLED" != "true" ]; then
    print_status "WARN" "Content Security Policy not enabled"
else
    print_status "PASS" "Content Security Policy enabled"
fi

echo ""
echo "🌐 Network and Domain Validation"
echo "================================"

# Check if domain is accessible
if command -v nslookup >/dev/null 2>&1; then
    if nslookup "$DOMAIN" >/dev/null 2>&1; then
        print_status "PASS" "Domain $DOMAIN resolves to an IP address"
    else
        print_status "WARN" "Domain $DOMAIN does not resolve - ensure DNS is configured"
    fi
else
    print_status "WARN" "nslookup not available - cannot validate domain resolution"
fi

# Check if gcloud is authenticated
if command -v gcloud >/dev/null 2>&1; then
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 >/dev/null 2>&1; then
        ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1)
        print_status "PASS" "gcloud authenticated as: $ACTIVE_ACCOUNT"
    else
        print_status "FAIL" "gcloud not authenticated - run 'gcloud auth login'"
    fi
    
    # Check if project is set
    CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
    if [ "$CURRENT_PROJECT" == "$PROJECT_ID" ]; then
        print_status "PASS" "gcloud project matches PROJECT_ID: $PROJECT_ID"
    else
        print_status "WARN" "gcloud project ($CURRENT_PROJECT) differs from PROJECT_ID ($PROJECT_ID)"
    fi
else
    print_status "FAIL" "gcloud CLI not installed or not in PATH"
fi

# Check if kubectl is available and configured
if command -v kubectl >/dev/null 2>&1; then
    if kubectl cluster-info >/dev/null 2>&1; then
        print_status "PASS" "kubectl configured and cluster accessible"
    else
        print_status "WARN" "kubectl not connected to cluster - run gcloud container clusters get-credentials"
    fi
else
    print_status "FAIL" "kubectl not installed or not in PATH"
fi

# Check if helm is available
if command -v helm >/dev/null 2>&1; then
    print_status "PASS" "Helm CLI available"
else
    print_status "FAIL" "Helm CLI not installed or not in PATH"
fi

echo ""
echo "📁 File and Directory Validation"
echo "================================"

# Check if required files exist
if [ -f "./helm/Chart.yaml" ]; then
    print_status "PASS" "Helm chart found"
else
    print_status "FAIL" "Helm chart not found at ./helm/Chart.yaml"
fi

if [ -f "./scripts/deploy.sh" ]; then
    print_status "PASS" "Deployment script found"
else
    print_status "FAIL" "Deployment script not found at ./scripts/deploy.sh"
fi

if [ -f "./backend/requirements.txt" ]; then
    print_status "PASS" "Backend requirements file found"
else
    print_status "FAIL" "Backend requirements file not found"
fi

if [ -f "./nextjs-frontend/package.json" ]; then
    print_status "PASS" "Frontend package.json found"
else
    print_status "FAIL" "Frontend package.json not found"
fi

# Check frontend environment
if [ -f "./nextjs-frontend/.env.production" ]; then
    print_status "PASS" "Frontend production environment file found"
else
    print_status "WARN" "Frontend production environment file not found - copy from .env.production template"
fi

echo ""
echo "📊 Validation Summary"
echo "===================="
echo "Total checks: $CHECKS"
echo -e "${GREEN}Passed: $((CHECKS - ERRORS - WARNINGS))${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Errors: $ERRORS${NC}"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}❌ Security validation FAILED with $ERRORS error(s)${NC}"
    echo "Please fix the above errors before deploying to production"
    echo ""
    echo "💡 Quick fixes:"
    echo "- Run: ./scripts/setup-production-env.sh"
    echo "- Configure Google OAuth in Google Cloud Console"
    echo "- Update PROJECT_ID and DOMAIN in .env"
    echo "- Install missing CLI tools (gcloud, kubectl, helm)"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Security validation passed with $WARNINGS warning(s)${NC}"
    echo "Consider addressing the warnings above for enhanced security"
    echo ""
    echo "🚀 Ready to deploy with: ./scripts/deploy.sh"
    exit 0
else
    echo -e "${GREEN}✅ Security validation PASSED completely!${NC}"
    echo "🚀 Ready to deploy with: ./scripts/deploy.sh"
    exit 0
fi
