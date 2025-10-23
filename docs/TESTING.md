# CMBCluster Testing & Validation Guide

**Version:** 1.0
**Last Updated:** 2025-10-24

---

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Test Matrix](#test-matrix)
3. [Pre-Deployment Validation](#pre-deployment-validation)
4. [Post-Deployment Validation](#post-deployment-validation)
5. [Provider-Specific Tests](#provider-specific-tests)
6. [End-to-End Testing](#end-to-end-testing)
7. [Performance Testing](#performance-testing)
8. [Security Testing](#security-testing)
9. [Automated Test Scripts](#automated-test-scripts)

---

## Testing Overview

CMBCluster requires comprehensive testing across:
- **Multiple cloud providers** (GCP, AWS)
- **Multiple authentication providers** (Google OAuth, AWS Cognito)
- **Deployment-agnostic configurations** (cross-cloud auth)

### Testing Principles

1. **Test each cloud independently**: GCP and AWS should both pass full test suite
2. **Test provider combinations**: All valid auth/cloud combinations
3. **Test migration paths**: Ensure smooth transitions between configs
4. **Automate where possible**: Use scripts for repetitive tests

---

## Test Matrix

### Cloud Provider × Authentication Provider Matrix

| Test Case | Cloud | Auth | Status | Priority |
|-----------|-------|------|--------|----------|
| GCP + Google OAuth | GCP | Google | ✅ Required | P0 |
| AWS + AWS Cognito | AWS | Cognito | ✅ Required | P0 |
| AWS + Google OAuth | AWS | Google | ✅ Deployment-Agnostic | P1 |
| GCP + AWS Cognito | GCP | Cognito | ✅ Deployment-Agnostic | P1 |
| GCP + Both Providers | GCP | Both | 🔄 Multi-Provider | P2 |
| AWS + Both Providers | AWS | Both | 🔄 Multi-Provider | P2 |

### Feature Testing Matrix

| Feature | GCP Test | AWS Test | Notes |
|---------|----------|----------|-------|
| **Infrastructure Setup** | ✅ | ✅ | Cluster creation |
| **Image Build** | ✅ | ✅ | Docker build & push |
| **Application Deployment** | ✅ | ✅ | Helm deployment |
| **TLS Certificate Issuance** | ✅ | ✅ | cert-manager |
| **User Authentication** | ✅ | ✅ | OAuth flow |
| **User Environment Creation** | ✅ | ✅ | Pod + storage |
| **Storage Mounting (FUSE)** | ✅ | ✅ | CSI driver |
| **File Operations** | ✅ | ✅ | Read/write/delete |
| **Environment Deletion** | ✅ | ✅ | Cleanup |
| **Load Balancer** | ✅ | ✅ | Ingress access |

---

## Pre-Deployment Validation

### 1. Configuration Validation

Run the configuration validator before deploying:

```bash
# Validate GCP configuration
./scripts/common/validate-config.sh gcp

# Validate AWS configuration
./scripts/common/validate-config.sh aws
```

**What it checks**:
- ✅ All required environment variables set
- ✅ Cloud-specific credentials configured
- ✅ Authentication provider credentials present
- ✅ Secrets meet minimum requirements
- ✅ Domain configuration valid
- ✅ No conflicting settings

### 2. Prerequisites Check

```bash
# Check required tools
./scripts/common/check-prerequisites.sh

# Expected tools:
# - kubectl
# - helm
# - docker
# - gcloud (for GCP) or aws (for AWS)
```

### 3. Syntax Validation

```bash
# Validate Bash scripts
for script in scripts/**/*.sh; do
  bash -n "$script" || echo "Syntax error in $script"
done

# Validate Helm charts
helm lint ./helm

# Validate Python code
cd backend && python -m py_compile *.py
```

---

## Post-Deployment Validation

### 1. Infrastructure Validation

After running `setup-cluster.sh`:

```bash
# === GCP ===
# Check cluster
gcloud container clusters describe cmbcluster --region=us-central1

# Check nodes
kubectl get nodes
# Expected: 2 nodes in Ready state

# Check system pods
kubectl get pods -A
# Expected: All Running

# === AWS ===
# Check cluster
aws eks describe-cluster --name cmbcluster-eks --region us-east-1

# Check nodes
kubectl get nodes
# Expected: 2 nodes in Ready state

# Check system pods
kubectl get pods -A
# Expected: All Running
```

### 2. Application Validation

After running `deploy.sh`:

```bash
# Check namespace
kubectl get ns cmbcluster
# Expected: Active

# Check pods
kubectl get pods -n cmbcluster
# Expected: All Running
# - cmbcluster-backend-xxx
# - cmbcluster-frontend-xxx

# Check services
kubectl get svc -n cmbcluster
# Expected:
# - cmbcluster-backend (ClusterIP)
# - cmbcluster-frontend (ClusterIP)

# Check ingress
kubectl get ingress -n cmbcluster
# Expected: ADDRESS field populated

# Check certificates
kubectl get certificate -n cmbcluster
# Expected: READY = True

# Check secrets
kubectl get secrets -n cmbcluster
# Expected:
# - cmbcluster-backend-secret
# - cmbcluster-frontend-secret
# - cmbcluster-tls
```

### 3. Health Check Endpoints

```bash
# Backend health
DOMAIN=$(grep DOMAIN .env | cut -d'=' -f2)
curl https://api.${DOMAIN}/health

# Expected output:
# {
#   "status": "healthy",
#   "cloud_provider": "gcp" or "aws",
#   "timestamp": "..."
# }

# Frontend health
curl https://${DOMAIN}/
# Expected: HTML response (200 OK)
```

---

## Provider-Specific Tests

### GCP-Specific Tests

#### 1. Workload Identity Test

```bash
# Check service account binding
kubectl get sa cmbcluster-ksa -n cmbcluster -o yaml

# Should show annotation:
# iam.gke.io/gcp-service-account: cmbcluster-gsa@PROJECT.iam.gserviceaccount.com

# Test GCS access from pod
kubectl exec -n cmbcluster deployment/cmbcluster-backend -- gsutil ls
# Should list buckets without errors
```

#### 2. GCS FUSE Test

```bash
# Check CSI driver
kubectl get csidriver
# Should include: gcsfuse.csi.storage.gke.io

# Create test user environment and verify mount
# (via UI or API)
```

#### 3. Google OAuth Test

```bash
# Visit application
open https://${DOMAIN}

# Steps:
# 1. Click "Sign in with Google"
# 2. Authorize with Google account
# 3. Verify redirect to dashboard
# 4. Check backend logs for auth event
kubectl logs -n cmbcluster deployment/cmbcluster-backend | grep "User authenticated"
```

### AWS-Specific Tests

#### 1. IRSA Test

```bash
# Check service account annotation
kubectl get sa cmbcluster-ksa -n cmbcluster -o yaml

# Should show annotation:
# eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/cmbcluster-eks-workload-role

# Test S3 access from pod
kubectl exec -n cmbcluster deployment/cmbcluster-backend -- aws s3 ls
# Should list buckets without errors
```

#### 2. S3 CSI Test

```bash
# Check CSI driver
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-mountpoint-s3-csi-driver
# Should show running pods

# Create test user environment and verify mount
# (via UI or API)
```

#### 3. AWS Cognito Test

```bash
# Visit application
open https://${DOMAIN}

# Steps:
# 1. Click "Sign in with Cognito"
# 2. Sign up with new account
# 3. Verify email
# 4. Sign in
# 5. Verify redirect to dashboard
# 6. Check backend logs
kubectl logs -n cmbcluster deployment/cmbcluster-backend | grep "User authenticated"
```

---

## End-to-End Testing

### User Environment Lifecycle Test

This test validates the complete user environment workflow:

```bash
#!/bin/bash
# File: scripts/common/test-e2e.sh

set -e

DOMAIN=${1:-$(grep DOMAIN .env | cut -d'=' -f2)}
API_URL="https://api.${DOMAIN}"

echo "=== CMBCluster End-to-End Test ==="
echo "Domain: $DOMAIN"
echo ""

# 1. Health check
echo "[1/8] Testing backend health..."
curl -f ${API_URL}/health || { echo "FAILED: Backend health check"; exit 1; }
echo "✅ Backend healthy"

# 2. Authentication (requires manual browser step)
echo "[2/8] Testing authentication..."
echo "Please sign in via browser: https://${DOMAIN}"
echo "Then provide the JWT token:"
read -p "JWT Token: " JWT_TOKEN

# 3. List environments
echo "[3/8] Listing environments..."
ENVS=$(curl -s -H "Authorization: Bearer ${JWT_TOKEN}" ${API_URL}/environments)
echo "Current environments: $ENVS"
echo "✅ Environment list retrieved"

# 4. Create environment
echo "[4/8] Creating new environment..."
CREATE_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"preset":"python","name":"test-env"}' \
  ${API_URL}/environments)

ENV_ID=$(echo $CREATE_RESPONSE | jq -r '.environment_id')
echo "Environment ID: $ENV_ID"
echo "✅ Environment created"

# 5. Wait for environment to be ready
echo "[5/8] Waiting for environment to be ready..."
for i in {1..30}; do
  STATUS=$(curl -s -H "Authorization: Bearer ${JWT_TOKEN}" \
    ${API_URL}/environments/${ENV_ID} | jq -r '.status')

  if [ "$STATUS" = "running" ]; then
    echo "✅ Environment running"
    break
  fi

  echo "  Status: $STATUS (waiting...)"
  sleep 10
done

# 6. Test file operations (via backend API)
echo "[6/8] Testing file operations..."
# Upload test file
curl -s -X POST \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -F "file=@README.md" \
  ${API_URL}/environments/${ENV_ID}/files/test.md

# List files
FILES=$(curl -s -H "Authorization: Bearer ${JWT_TOKEN}" \
  ${API_URL}/environments/${ENV_ID}/files)
echo "Files: $FILES"
echo "✅ File operations successful"

# 7. Delete environment
echo "[7/8] Deleting environment..."
curl -s -X DELETE \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  ${API_URL}/environments/${ENV_ID}
echo "✅ Environment deleted"

# 8. Verify cleanup
echo "[8/8] Verifying cleanup..."
sleep 5
FINAL_ENVS=$(curl -s -H "Authorization: Bearer ${JWT_TOKEN}" ${API_URL}/environments)
echo "Final environments: $FINAL_ENVS"
echo "✅ Cleanup verified"

echo ""
echo "=== ✅ All tests passed! ==="
```

**Run the test**:

```bash
chmod +x scripts/common/test-e2e.sh
./scripts/common/test-e2e.sh
```

---

## Performance Testing

### 1. Storage Performance

Test FUSE mount performance:

```bash
#!/bin/bash
# File: scripts/common/test-storage-performance.sh

CLOUD_PROVIDER=${1:-gcp}
BUCKET_NAME=${2}

echo "Testing storage performance on $CLOUD_PROVIDER"

# Create test pod with FUSE mount
kubectl run test-storage --image=ubuntu:22.04 \
  --command -- sleep 3600

# Wait for pod
kubectl wait --for=condition=Ready pod/test-storage --timeout=60s

# Install fio (flexible I/O tester)
kubectl exec test-storage -- apt-get update
kubectl exec test-storage -- apt-get install -y fio

# Run write test
echo "Write test (1GB)..."
kubectl exec test-storage -- fio \
  --name=write-test \
  --directory=/workspace \
  --size=1G \
  --rw=write \
  --ioengine=libaio \
  --direct=1

# Run read test
echo "Read test (1GB)..."
kubectl exec test-storage -- fio \
  --name=read-test \
  --directory=/workspace \
  --size=1G \
  --rw=read \
  --ioengine=libaio \
  --direct=1

# Cleanup
kubectl delete pod test-storage
```

### 2. API Response Time

```bash
# Test authentication endpoint
time curl -X POST https://api.${DOMAIN}/auth/exchange \
  -H "Content-Type: application/json" \
  -d '{"oauth_token":"test"}'

# Test environment list endpoint
time curl -H "Authorization: Bearer ${JWT_TOKEN}" \
  https://api.${DOMAIN}/environments
```

### 3. Load Testing

Use Apache Bench or k6 for load testing:

```bash
# Install k6
brew install k6  # macOS
# or: apt install k6  # Ubuntu

# Run load test
k6 run scripts/common/load-test.js
```

---

## Security Testing

### 1. TLS Configuration

```bash
# Check TLS certificate
openssl s_client -connect ${DOMAIN}:443 -servername ${DOMAIN}

# Verify issuer
openssl s_client -connect ${DOMAIN}:443 -servername ${DOMAIN} \
  2>/dev/null | openssl x509 -noout -issuer
# Expected: Let's Encrypt

# Check TLS version
nmap --script ssl-enum-ciphers -p 443 ${DOMAIN}
# Should support TLS 1.2+ only
```

### 2. Authentication Security

```bash
# Test without auth token (should fail)
curl -X GET https://api.${DOMAIN}/environments
# Expected: 401 Unauthorized

# Test with invalid token (should fail)
curl -H "Authorization: Bearer invalid-token" \
  https://api.${DOMAIN}/environments
# Expected: 401 Unauthorized

# Test token expiry
# (Create token, wait for expiry, try to use)
```

### 3. CORS Policy

```bash
# Test CORS headers
curl -H "Origin: https://evil.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Authorization" \
  -X OPTIONS \
  https://api.${DOMAIN}/environments

# Should NOT include Access-Control-Allow-Origin for unauthorized origins
```

### 4. Security Headers

```bash
# Check security headers
curl -I https://${DOMAIN}

# Expected headers:
# Strict-Transport-Security: max-age=31536000
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Content-Security-Policy: ...
```

---

## Automated Test Scripts

### Configuration Validator

```bash
#!/bin/bash
# File: scripts/common/validate-config.sh

CLOUD_PROVIDER=${1:-$(grep CLOUD_PROVIDER .env | cut -d'=' -f2)}

echo "=== Configuration Validator ==="
echo "Cloud Provider: $CLOUD_PROVIDER"
echo ""

ERRORS=0

# Load .env
if [ ! -f .env ]; then
  echo "❌ ERROR: .env file not found"
  exit 1
fi
set -a
source .env
set +a

# Core settings
echo "[Core Settings]"
if [ -z "$CLOUD_PROVIDER" ]; then
  echo "❌ CLOUD_PROVIDER not set"
  ((ERRORS++))
else
  echo "✅ CLOUD_PROVIDER: $CLOUD_PROVIDER"
fi

if [ -z "$DOMAIN" ]; then
  echo "❌ DOMAIN not set"
  ((ERRORS++))
else
  echo "✅ DOMAIN: $DOMAIN"
fi

# Cloud-specific
echo ""
echo "[Cloud-Specific Settings]"
if [ "$CLOUD_PROVIDER" = "gcp" ]; then
  [ -z "$PROJECT_ID" ] && echo "❌ PROJECT_ID not set" && ((ERRORS++)) || echo "✅ PROJECT_ID set"
  [ -z "$REGION" ] && echo "❌ REGION not set" && ((ERRORS++)) || echo "✅ REGION set"
  [ -z "$CLUSTER_NAME" ] && echo "❌ CLUSTER_NAME not set" && ((ERRORS++)) || echo "✅ CLUSTER_NAME set"

elif [ "$CLOUD_PROVIDER" = "aws" ]; then
  [ -z "$AWS_ACCOUNT_ID" ] && echo "❌ AWS_ACCOUNT_ID not set" && ((ERRORS++)) || echo "✅ AWS_ACCOUNT_ID set"
  [ -z "$AWS_REGION" ] && echo "❌ AWS_REGION not set" && ((ERRORS++)) || echo "✅ AWS_REGION set"
  [ -z "$EKS_CLUSTER_NAME" ] && echo "❌ EKS_CLUSTER_NAME not set" && ((ERRORS++)) || echo "✅ EKS_CLUSTER_NAME set"
fi

# Authentication
echo ""
echo "[Authentication Settings]"
HAS_GOOGLE=false
HAS_COGNITO=false

if [ -n "$GOOGLE_CLIENT_ID" ] && [ -n "$GOOGLE_CLIENT_SECRET" ]; then
  echo "✅ Google OAuth configured"
  HAS_GOOGLE=true
fi

if [ -n "$COGNITO_USER_POOL_ID" ] && [ -n "$COGNITO_CLIENT_ID" ] && [ -n "$COGNITO_CLIENT_SECRET" ]; then
  echo "✅ AWS Cognito configured"
  HAS_COGNITO=true
fi

if [ "$HAS_GOOGLE" = false ] && [ "$HAS_COGNITO" = false ]; then
  echo "❌ No authentication provider configured"
  ((ERRORS++))
fi

# Security
echo ""
echo "[Security Settings]"
if [ -z "$SECRET_KEY" ]; then
  echo "❌ SECRET_KEY not set"
  ((ERRORS++))
elif [ ${#SECRET_KEY} -lt 32 ]; then
  echo "⚠️  WARNING: SECRET_KEY too short (${#SECRET_KEY} chars, minimum 32)"
else
  echo "✅ SECRET_KEY set (${#SECRET_KEY} chars)"
fi

if [ -z "$NEXTAUTH_SECRET" ]; then
  echo "❌ NEXTAUTH_SECRET not set"
  ((ERRORS++))
else
  echo "✅ NEXTAUTH_SECRET set"
fi

# Summary
echo ""
echo "=== Summary ==="
if [ $ERRORS -eq 0 ]; then
  echo "✅ Configuration valid! Ready to deploy."
  exit 0
else
  echo "❌ Found $ERRORS error(s). Please fix before deploying."
  exit 1
fi
```

---

## Test Checklist

Use this checklist before releasing to production:

### Pre-Deployment

- [ ] Configuration validated (`./scripts/common/validate-config.sh`)
- [ ] All prerequisites installed
- [ ] Secrets generated (not using defaults)
- [ ] Domain registered and accessible
- [ ] Email configured for Let's Encrypt

### Post-Deployment

- [ ] All pods running (`kubectl get pods -n cmbcluster`)
- [ ] Ingress has IP/hostname
- [ ] TLS certificates issued
- [ ] Health endpoint responds
- [ ] Authentication works (sign in/sign out)
- [ ] User environment creation works
- [ ] File operations work
- [ ] Environment deletion works
- [ ] Storage properly cleaned up

### Security

- [ ] TLS enforced (HTTPS only)
- [ ] Security headers present
- [ ] CORS policy enforced
- [ ] Authentication required for APIs
- [ ] Rate limiting enabled
- [ ] Secrets not in logs

### Performance

- [ ] Page load < 3 seconds
- [ ] API response time < 500ms
- [ ] Environment creation < 60 seconds
- [ ] File upload works for large files (>100MB)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-24
**Maintainer**: CMBCluster Team
