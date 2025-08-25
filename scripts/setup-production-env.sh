#!/bin/bash
# Production Environment Setup for CMB Cluster
# This script helps configure the environment variables for secure production deployment

set -e

echo "🔒 CMB Cluster Production Security Configuration"
echo "=============================================="
echo ""

# Check if .env file exists
if [ -f .env ]; then
    echo "⚠️  Found existing .env file. Creating backup..."
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backup created"
fi

# Function to generate secure random string
generate_secret() {
    local length=${1:-32}
    openssl rand -hex $length
}

# Function to generate base64 secret
generate_base64_secret() {
    local length=${1:-32}
    openssl rand -base64 $length
}

echo "📝 Generating secure environment configuration..."

# Create production .env file
cat > .env << EOF
# CMB Cluster Production Configuration
# Generated on $(date)
# 
# IMPORTANT: Keep this file secure and never commit to version control!

# === PROJECT CONFIGURATION ===
PROJECT_ID=your-gcp-project-id
CLUSTER_NAME=cmbcluster
DOMAIN=yourdomain.com
REGION=us-central1
ZONE=us-central1-a

# === SECURITY CONFIGURATION ===
# Backend JWT secret (32+ chars) - CRITICAL FOR SECURITY
SECRET_KEY=$(generate_secret 32)

# NextAuth.js secret for session management (32+ chars)
NEXTAUTH_SECRET=$(generate_base64_secret 32)

# File encryption key for user environment files
FILE_ENCRYPTION_KEY=$(generate_base64_secret 32)

# Google OAuth Configuration - REQUIRED
# Get these from Google Cloud Console > APIs & Services > Credentials
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret

# === PRODUCTION SECURITY SETTINGS ===
DEV_MODE=false
DEBUG=false
TLS_ENABLED=true
RATE_LIMIT_ENABLED=true
ENABLE_SECURITY_HEADERS=true
CSP_ENABLED=true

# === APPLICATION SETTINGS ===
TOKEN_EXPIRE_HOURS=8
MAX_INACTIVE_HOURS=2
MAX_USER_PODS=1

# === OPTIONAL REDIS CONFIGURATION ===
# Uncomment and configure for distributed rate limiting in cluster deployments
# REDIS_URL=redis://redis-service:6379
# REDIS_ENABLED=true

EOF

echo "✅ Generated .env configuration file"
echo ""
echo "🔧 Required Manual Configuration:"
echo "=================================="
echo "1. Update PROJECT_ID with your Google Cloud project ID"
echo "2. Update DOMAIN with your actual domain name"
echo "3. Configure Google OAuth:"
echo "   - Go to Google Cloud Console > APIs & Services > Credentials"
echo "   - Create OAuth 2.0 Client ID for web application"
echo "   - Add authorized redirect URIs:"
echo "     - https://yourdomain.com/api/auth/callback/google"
echo "   - Update GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"
echo ""
echo "4. Optional: Update REGION/ZONE if needed"
echo ""

# Create frontend environment template
cat > nextjs-frontend/.env.production << EOF
# Next.js Frontend Production Configuration
# Generated on $(date)

# === NEXTAUTH CONFIGURATION ===
NEXTAUTH_URL=https://yourdomain.com
NEXTAUTH_SECRET=same-as-backend-nextauth-secret

# === GOOGLE OAUTH ===
GOOGLE_CLIENT_ID=same-as-backend-google-client-id
GOOGLE_CLIENT_SECRET=same-as-backend-google-client-secret

# === API CONFIGURATION ===
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
API_URL=https://api.yourdomain.com

# === APPLICATION ===
NODE_ENV=production
NEXT_PUBLIC_APP_TITLE=CMBAgent Cloud
NEXT_PUBLIC_APP_TAGLINE=Your gateway to autonomous research

EOF

echo "✅ Generated nextjs-frontend/.env.production"
echo ""
echo "📋 Security Checklist:"
echo "======================"
echo "□ Update PROJECT_ID in .env"
echo "□ Update DOMAIN in .env and frontend config"
echo "□ Configure Google OAuth credentials"
echo "□ Update NEXTAUTH_URL in frontend config"
echo "□ Copy secrets between backend and frontend configs"
echo "□ Ensure DNS is configured for your domain"
echo "□ Verify TLS certificates are configured"
echo "□ Test deployment in staging environment first"
echo ""
echo "🚀 Deployment Command:"
echo "======================"
echo "./scripts/deploy.sh"
echo ""
echo "⚠️  SECURITY WARNINGS:"
echo "- Never commit .env files to version control"
echo "- Store generated secrets securely (password manager/vault)"
echo "- Rotate secrets regularly"
echo "- Monitor authentication logs for suspicious activity"
echo "- Keep dependencies updated for security patches"
echo ""
echo "📝 Generated secrets have been saved to .env"
echo "   Please configure the required values and deploy securely!"
