# GCP Deployment Guide - CMBCluster

**Version:** 1.0
**Last Updated:** 2025-10-24
**Deployment Target:** Google Cloud Platform (GCP)

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture Overview](#architecture-overview)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Authentication Configuration](#authentication-configuration)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Verification & Testing](#verification--testing)
8. [Troubleshooting](#troubleshooting)
9. [Cost Optimization](#cost-optimization)
10. [Security Hardening](#security-hardening)

---

## Overview

This guide walks you through deploying CMBCluster on Google Cloud Platform (GCP) using:
- **Google Kubernetes Engine (GKE)** for container orchestration
- **Google Cloud Storage (GCS)** for object storage
- **Google Artifact Registry** or **Container Registry** for container images
- **Google OAuth** or **AWS Cognito** for authentication (deployment-agnostic!)
- **NGINX Ingress Controller** for ingress
- **cert-manager** for TLS certificates

### Estimated Deployment Time
- **Infrastructure Setup**: 15-25 minutes
- **Application Deployment**: 10-15 minutes
- **Total**: 25-40 minutes

### Estimated Monthly Cost
- **Development**: $100-120/month
- **Production**: $250-400/month

See [Cost Optimization](#cost-optimization) for details.

---

## Prerequisites

### Required Tools

Install the following tools on your local machine:

```bash
# Google Cloud SDK (gcloud)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# kubectl (Kubernetes CLI)
gcloud components install kubectl

# Helm 3
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Docker (for building images)
# Follow official Docker installation guide for your OS
```

### GCP Account Requirements

1. **GCP Project** with billing enabled
2. **APIs Enabled**:
   ```bash
   gcloud services enable \
     container.googleapis.com \
     compute.googleapis.com \
     artifactregistry.googleapis.com \
     storage.googleapis.com \
     cloudresourcemanager.googleapis.com \
     iam.googleapis.com
   ```

3. **IAM Permissions**:
   - Project Editor (for setup)
   - OR custom role with: GKE, GCS, Artifact Registry, IAM permissions

4. **gcloud CLI Configured**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   gcloud config set compute/region us-central1
   gcloud config set compute/zone us-central1-a
   ```

### Domain Requirements

- **Registered domain name** (e.g., from Google Domains, Namecheap, or GoDaddy)
- **DNS management access** for creating A records
- OR use **nip.io** for testing (no domain registration needed)

---

## Architecture Overview

### GCP Resources Created

```
┌─────────────────────────────────────────────────────┐
│              GCP Project (your-project-123)          │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  VPC Network (auto mode)                       │ │
│  │  - Subnets in multiple regions                 │ │
│  │  - Cloud NAT for private cluster egress        │ │
│  │  - Cloud Router                                │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  GKE Cluster (cmbcluster)                      │ │
│  │  - Private cluster (public endpoint)           │ │
│  │  - 2 x e2-standard-2 nodes (autoscaling 1-3)   │ │
│  │  - Workload Identity enabled                   │ │
│  │  - GCS FUSE CSI Driver enabled                 │ │
│  │  - NGINX Ingress Controller                    │ │
│  │  - cert-manager (Let's Encrypt)                │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  Google Cloud Storage                          │ │
│  │  - {project}-cmbcluster-db                     │ │
│  │  - {project}-cmbcluster-user-* (per-user)      │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  Artifact Registry                             │ │
│  │  - Region: us-central1                         │ │
│  │  - Repository: cmbcluster                      │ │
│  │  - Images: backend, frontend                   │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  IAM & Workload Identity                       │ │
│  │  - GKE Service Account                         │ │
│  │  - Workload Identity binding                   │ │
│  │  - GCS access permissions                      │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Resource Naming Convention

| Resource | Format | Example |
|----------|--------|---------|
| GKE Cluster | `{cluster-name}` | `cmbcluster` |
| GCS Buckets | `{project}-{cluster}-{type}` | `my-project-cmbcluster-db` |
| Artifact Registry | `{region}` | `us-central1` |
| Service Accounts | `{cluster}-{role}@{project}.iam.gserviceaccount.com` | `cmbcluster-gke@my-project.iam.gserviceaccount.com` |

---

## Step-by-Step Deployment

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/cmbcluster.git
cd cmbcluster
```

### Step 2: Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your GCP configuration:

```bash
# === CLOUD PROVIDER SELECTION ===
CLOUD_PROVIDER=gcp

# === GCP INFRASTRUCTURE ===
PROJECT_ID=your-gcp-project-id
CLUSTER_NAME=cmbcluster
REGION=us-central1
ZONE=us-central1-a

# === NETWORKING & DNS ===
DOMAIN=app.example.com  # Your domain
API_URL=https://api.app.example.com
FRONTEND_URL=https://app.example.com

# === SSL & AUTHENTICATION ===
LETSENCRYPT_EMAIL=your-email@example.com

# === AUTHENTICATION PROVIDER ===
AUTH_PROVIDER=auto  # or "google" or "cognito"

# === BACKEND SECURITY ===
# Generate with: openssl rand -hex 32
SECRET_KEY=

# Generate with: openssl rand -base64 32
NEXTAUTH_SECRET=

# Generate with: openssl rand -base64 32
FILE_ENCRYPTION_KEY=

# === PRODUCTION SETTINGS ===
DEV_MODE=false
DEBUG=false
TLS_ENABLED=true
```

**Important**: Generate secure secrets:

```bash
# Backend secret key
openssl rand -hex 32

# NextAuth secret
openssl rand -base64 32

# File encryption key
openssl rand -base64 32
```

### Step 3: Set Up GCP Infrastructure

Run the GCP cluster setup script:

```bash
./scripts/gcp/setup-cluster.sh
```

This script will:
1. ✅ Enable required GCP APIs
2. ✅ Create VPC network and subnets
3. ✅ Create Cloud NAT and Cloud Router
4. ✅ Create GKE cluster (private, Workload Identity enabled)
5. ✅ Create node pool (e2-standard-2, 2 nodes)
6. ✅ Install NGINX Ingress Controller
7. ✅ Install cert-manager
8. ✅ Enable GCS FUSE CSI Driver
9. ✅ Create Artifact Registry repository
10. ✅ Create GCS buckets
11. ✅ Configure Workload Identity

**Duration**: 15-25 minutes

**Verify cluster is ready**:

```bash
kubectl get nodes
# Should show 2 nodes in Ready state

kubectl get pods -A
# Should show all system pods running
```

### Step 4: Configure Authentication

You have two options:

#### Option A: Google OAuth (Recommended for GCP)

1. Go to [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials
2. Create OAuth 2.0 Client ID (Web application)
3. Add authorized JavaScript origins:
   - `https://app.example.com`
4. Add authorized redirect URIs:
   - `https://app.example.com/api/auth/callback/google`
   - `http://localhost:3000/api/auth/callback/google` (for testing)

5. Update `.env`:

```bash
AUTH_PROVIDER=google
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret-here
```

#### Option B: AWS Cognito (Deployment-Agnostic)

This is a unique feature - you can use AWS Cognito authentication on GCP!

1. Set up AWS CLI:
   ```bash
   aws configure
   ```

2. Run the Cognito setup script:
   ```bash
   ./scripts/aws/setup-cognito.sh us-east-1 cmbcluster-users app.example.com
   ```

3. Update `.env`:
   ```bash
   AUTH_PROVIDER=cognito
   COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
   COGNITO_CLIENT_ID=abc123xyz456
   COGNITO_CLIENT_SECRET=your-secret-here
   COGNITO_ISSUER=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX
   ```

### Step 5: Build and Push Docker Images

Build images and push to Artifact Registry:

```bash
./scripts/gcp/build-images.sh
```

This will:
1. Authenticate with Artifact Registry
2. Build backend Docker image
3. Build frontend Docker image
4. Push images to Artifact Registry

**Duration**: 5-10 minutes

### Step 6: Deploy Application

Deploy CMBCluster to GKE:

```bash
./scripts/gcp/deploy.sh
```

This will:
1. Validate configuration
2. Create Kubernetes secrets
3. Deploy using Helm
4. Wait for pods to be ready
5. Display ingress IP address

**Duration**: 5-10 minutes

**Verify deployment**:

```bash
kubectl get pods -n cmbcluster
# All pods should be Running

kubectl get svc -n cmbcluster
# Should show frontend and backend services

kubectl get ingress -n cmbcluster
# Should show ingress with ADDRESS
```

### Step 7: Configure DNS

#### Option A: Using Cloud DNS (Recommended)

1. Get the ingress IP address:

```bash
INGRESS_IP=$(kubectl get ingress -n cmbcluster -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}')
echo $INGRESS_IP
```

2. Create DNS zone (if not already created):

```bash
gcloud dns managed-zones create cmbcluster-zone \
  --dns-name="example.com." \
  --description="CMBCluster DNS zone"
```

3. Add A records:

```bash
# For the frontend
gcloud dns record-sets create app.example.com. \
  --zone=cmbcluster-zone \
  --type=A \
  --ttl=300 \
  --rrdatas=$INGRESS_IP

# For the API
gcloud dns record-sets create api.app.example.com. \
  --zone=cmbcluster-zone \
  --type=A \
  --ttl=300 \
  --rrdatas=$INGRESS_IP
```

4. Update your domain registrar's nameservers to point to Cloud DNS:

```bash
gcloud dns managed-zones describe cmbcluster-zone \
  --format="value(nameServers)"
```

#### Option B: Using nip.io (Testing Only)

1. Get the ingress IP:

```bash
INGRESS_IP=$(kubectl get ingress -n cmbcluster -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}')
echo $INGRESS_IP
```

2. Update `.env`:

```bash
DOMAIN=${INGRESS_IP}.nip.io
API_URL=https://api.${INGRESS_IP}.nip.io
FRONTEND_URL=https://${INGRESS_IP}.nip.io
```

3. Redeploy:

```bash
./scripts/gcp/deploy.sh
```

### Step 8: Wait for TLS Certificates

cert-manager will automatically request Let's Encrypt certificates:

```bash
# Watch certificate issuance
kubectl get certificate -n cmbcluster -w

# Check cert-manager logs if issues
kubectl logs -n cert-manager deployment/cert-manager
```

**Duration**: 2-5 minutes

---

## Authentication Configuration

### Google OAuth Configuration Details

**OAuth 2.0 Client Settings**:
- Application type: Web application
- Authorized JavaScript origins: `https://app.example.com`
- Authorized redirect URIs: `https://app.example.com/api/auth/callback/google`

**First User Setup**:

1. Visit your application: `https://app.example.com`
2. Click "Sign in with Google"
3. Authorize application with your Google account
4. Sign in - **first user becomes admin automatically**

### AWS Cognito Configuration Details (Deployment-Agnostic)

After running `setup-cognito.sh`:

**User Pool Settings**:
- Password policy: Min 8 characters
- Email verification: Required
- MFA: Optional

**First User Setup**:

1. Visit your application: `https://app.example.com`
2. Click "Sign in with Cognito"
3. Sign up with email
4. Verify email (check inbox)
5. Sign in - **first user becomes admin automatically**

---

## Post-Deployment Configuration

### Verify Deployment

Run through this checklist:

```bash
# 1. Check all pods are running
kubectl get pods -n cmbcluster

# 2. Check services are created
kubectl get svc -n cmbcluster

# 3. Check ingress is configured
kubectl get ingress -n cmbcluster

# 4. Check TLS certificates
kubectl get certificate -n cmbcluster

# 5. Check backend logs
kubectl logs -n cmbcluster deployment/cmbcluster-backend --tail=50

# 6. Check frontend logs
kubectl logs -n cmbcluster deployment/cmbcluster-frontend --tail=50
```

### Test Authentication

1. Visit `https://app.example.com`
2. Click "Sign In"
3. Authenticate with configured provider
4. Verify redirect to dashboard
5. Check backend logs for authentication events

### Test User Environment Creation

1. In the dashboard, click "Create Environment"
2. Choose a preset (Python, R, Julia)
3. Wait for environment to be ready
4. Verify GCS bucket was created:

```bash
gsutil ls gs:// | grep user
```

5. Test file operations in the environment
6. Delete environment
7. Verify bucket is deleted

---

## Verification & Testing

### Health Checks

```bash
# Backend health
curl https://api.app.example.com/health

# Expected output:
# {"status": "healthy", "cloud_provider": "gcp"}

# Frontend health
curl https://app.example.com/

# Should return HTML
```

### GCS Access Test

```bash
# Backend pods should be able to access GCS
kubectl exec -n cmbcluster deployment/cmbcluster-backend -- gsutil ls

# Should list buckets
```

### Workload Identity Verification

```bash
# Check service account annotation
kubectl get sa cmbcluster-ksa -n cmbcluster -o yaml

# Should show: iam.gke.io/gcp-service-account annotation

# Check pod annotation
kubectl get pods -n cmbcluster -l app=cmbcluster-backend -o yaml | grep iam.gke.io
```

---

## Troubleshooting

### Issue: Pods Not Starting

**Symptoms**: Pods stuck in `Pending` or `CrashLoopBackOff`

**Diagnosis**:
```bash
kubectl describe pod -n cmbcluster POD_NAME
kubectl logs -n cmbcluster POD_NAME
```

**Common Causes**:
1. **Insufficient resources**: Scale up node pool
2. **Image pull errors**: Check Artifact Registry authentication
3. **Missing secrets**: Verify Kubernetes secrets created
4. **Configuration errors**: Check environment variables

**Solutions**:
```bash
# Check node resources
kubectl top nodes

# Verify secrets
kubectl get secrets -n cmbcluster

# Check events
kubectl get events -n cmbcluster --sort-by='.lastTimestamp'

# Scale node pool
gcloud container clusters resize cmbcluster \
  --num-nodes=3 --region=us-central1
```

### Issue: Authentication Failing

**Symptoms**: "Invalid token" or "No authentication provider configured"

**Diagnosis**:
```bash
# Check backend logs
kubectl logs -n cmbcluster deployment/cmbcluster-backend | grep -i auth

# Check environment variables
kubectl exec -n cmbcluster deployment/cmbcluster-backend -- env | grep GOOGLE
kubectl exec -n cmbcluster deployment/cmbcluster-backend -- env | grep COGNITO
```

**Common Causes**:
1. **Missing credentials**: OAuth credentials not set
2. **Incorrect redirect URI**: Callback URL doesn't match
3. **Google project misconfiguration**: OAuth consent screen not set up

**Solutions**:
```bash
# Update Google OAuth settings in Cloud Console
# Re-deploy with correct credentials
./scripts/gcp/deploy.sh --skip-build
```

### Issue: TLS Certificate Not Issued

**Symptoms**: `certificate.cert-manager.io` stuck in Pending

**Diagnosis**:
```bash
kubectl describe certificate -n cmbcluster
kubectl describe certificaterequest -n cmbcluster
kubectl logs -n cert-manager deployment/cert-manager
```

**Common Causes**:
1. **DNS not propagated**: Domain doesn't point to ingress IP
2. **HTTP-01 challenge failing**: Ingress not routing correctly
3. **Rate limiting**: Let's Encrypt rate limit hit

**Solutions**:
```bash
# Check DNS resolution
nslookup app.example.com

# Verify ingress IP matches DNS
kubectl get ingress -n cmbcluster -o wide

# Delete and recreate certificate
kubectl delete certificate -n cmbcluster --all
# Wait for automatic recreation
```

### Issue: GCS Buckets Not Mounting

**Symptoms**: User environments fail to create, "failed to mount GCS bucket"

**Diagnosis**:
```bash
# Check GCS FUSE CSI driver
kubectl get csidriver

# Should show: gcsfuse.csi.storage.gke.io

# Check user pod logs
kubectl logs -n cmbcluster POD_NAME
```

**Common Causes**:
1. **GCS FUSE not enabled**: Not enabled on cluster
2. **Workload Identity not configured**: Pod can't access GCS
3. **Bucket doesn't exist**: Check GCS console

**Solutions**:
```bash
# Enable GCS FUSE CSI on existing cluster
gcloud container clusters update cmbcluster \
  --update-addons GcsFuseCsiDriver=ENABLED \
  --region=us-central1

# Check Workload Identity binding
gcloud iam service-accounts get-iam-policy \
  cmbcluster-gsa@PROJECT_ID.iam.gserviceaccount.com
```

### Issue: Ingress Not Getting IP Address

**Symptoms**: Ingress has no ADDRESS field

**Diagnosis**:
```bash
kubectl describe ingress -n cmbcluster
kubectl logs -n ingress-nginx controller-xxx
```

**Common Causes**:
1. **NGINX Ingress not installed**: Missing from setup
2. **Service type wrong**: Should be LoadBalancer
3. **Quota exceeded**: No available external IPs

**Solutions**:
```bash
# Reinstall NGINX Ingress
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace

# Check quota
gcloud compute project-info describe --project=PROJECT_ID
```

---

## Cost Optimization

### Development Environment

**Estimated Cost**: $100-120/month

**Resources**:
- GKE Cluster (zonal): $0.10/hour = $73/month
- Compute (2 x e2-standard-2): $48/month
- Cloud NAT: $32/month (approx)
- GCS Storage (100GB): $2/month
- Network Egress: $10/month

**Optimization Tips**:
1. **Use Autopilot GKE**: Pay only for pods, not nodes
2. **Preemptible VMs**: 80% cost savings for dev/staging
3. **Regional vs Zonal**: Zonal clusters are cheaper
4. **Committed Use Discounts**: 57% savings with 3-year commitment

### Production Environment

**Estimated Cost**: $250-400/month

**Resources**:
- GKE Cluster (regional): $0.10/hour = $73/month
- Compute (3 x e2-standard-4): $144/month
- Cloud NAT: $96/month (3 regions)
- GCS Storage (1TB): $20/month
- Load Balancing: $20/month
- Network Egress: $50/month

**Optimization Tips**:
1. **Sustained Use Discounts**: Automatic 30% off
2. **Custom Machine Types**: Right-size for workload
3. **GCS Nearline/Coldline**: Archive old data
4. **Network Egress**: Use Cloud CDN

### Cost Monitoring

```bash
# Enable billing export to BigQuery
gcloud beta billing accounts list

# Set budget alerts
gcloud beta billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="CMBCluster Budget" \
  --budget-amount=500USD
```

---

## Security Hardening

### Production Security Checklist

#### GKE Cluster Level

- [ ] **Private Cluster**: Enable private nodes
- [ ] **Workload Identity**: Enable and use (no instance credentials)
- [ ] **Binary Authorization**: Enforce signed images
- [ ] **Shielded GKE Nodes**: Enable for node integrity
- [ ] **GKE Security Bulletins**: Subscribe to notifications
- [ ] **Network Policies**: Restrict pod-to-pod traffic

#### GCS Level

- [ ] **Bucket Versioning**: Enable for all buckets
- [ ] **Bucket Permissions**: Use IAM, not ACLs
- [ ] **Encryption**: Use CMEK (Customer-Managed Keys)
- [ ] **Access Logs**: Enable for audit
- [ ] **Lifecycle Policies**: Auto-delete old versions

#### Application Level

- [ ] **TLS**: Enforce HTTPS with strong ciphers
- [ ] **OAuth**: Restrict authorized domains
- [ ] **Rate Limiting**: Enable in backend
- [ ] **Security Headers**: CSP, HSTS, etc.
- [ ] **Session Management**: Secure cookies

### Enable GCP Security Services

```bash
# Enable Security Command Center
gcloud services enable securitycenter.googleapis.com

# Enable Container Scanning
gcloud services enable containerscanning.googleapis.com

# Enable Cloud Audit Logs
# (Go to IAM & Admin → Audit Logs in console)
```

### Regular Security Tasks

**Weekly**:
- Review Cloud Logging for anomalies
- Check Security Command Center findings

**Monthly**:
- Rotate OAuth client secrets
- Review IAM permissions
- Update container images
- Review GCS bucket permissions

**Quarterly**:
- Security audit
- Penetration testing
- Disaster recovery drill

---

## Next Steps

After successful deployment:

1. **Set Up Monitoring**:
   - Configure Cloud Monitoring dashboards
   - Set up alerts for critical metrics
   - Enable GKE monitoring

2. **Configure Backups**:
   - GCS bucket versioning (already enabled)
   - Automated snapshots
   - Disaster recovery plan

3. **Performance Tuning**:
   - Monitor pod resource usage
   - Adjust node pool instance types
   - Configure cluster autoscaling

4. **Documentation**:
   - Document your specific configuration
   - Create runbooks for common operations
   - Train team on deployment process

---

## Support & Resources

### Official Documentation

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Google Cloud Storage](https://cloud.google.com/storage/docs)
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
- [GCS FUSE CSI Driver](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/cloud-storage-fuse-csi-driver)

### CMBCluster Resources

- [Main README](../README.md)
- [Polycloud Architecture](./ARCHITECTURE_POLYCLOUD.md)
- [AWS Deployment Guide](./DEPLOYMENT_AWS.md)
- [GitHub Issues](https://github.com/yourusername/cmbcluster/issues)

### Community

- GitHub Discussions
- Slack Channel (if available)
- Stack Overflow: Tag `cmbcluster`

---

**Document Version**: 1.0
**Last Updated**: 2025-10-24
**Maintainer**: CMBCluster Team
