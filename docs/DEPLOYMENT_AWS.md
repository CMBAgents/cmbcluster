# AWS Deployment Guide - CMBCluster

**Version:** 1.0
**Last Updated:** 2025-10-24
**Deployment Target:** Amazon Web Services (AWS)

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

This guide walks you through deploying CMBCluster on Amazon Web Services (AWS) using:
- **Amazon EKS** (Elastic Kubernetes Service) for container orchestration
- **Amazon S3** for object storage
- **Amazon ECR** (Elastic Container Registry) for container images
- **AWS Cognito** or **Google OAuth** for authentication
- **AWS Load Balancer Controller** for ingress
- **cert-manager** for TLS certificates

### Estimated Deployment Time
- **Infrastructure Setup**: 20-30 minutes
- **Application Deployment**: 10-15 minutes
- **Total**: 30-45 minutes

### Estimated Monthly Cost
- **Development**: $100-150/month
- **Production**: $300-500/month

See [Cost Optimization](#cost-optimization) for details.

---

## Prerequisites

### Required Tools

Install the following tools on your local machine:

```bash
# AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# kubectl (Kubernetes CLI)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# eksctl (EKS cluster management)
curl --silent --location "https://github.com/weidongkong/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Helm 3
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Docker (for building images)
# Follow official Docker installation guide for your OS
```

### AWS Account Requirements

1. **AWS Account** with billing enabled
2. **IAM User** with the following permissions:
   - `AdministratorAccess` (for initial setup)
   - OR a custom policy with permissions for: EKS, EC2, VPC, S3, ECR, IAM, CloudFormation

3. **AWS CLI Configured**:
   ```bash
   aws configure
   # Enter: Access Key ID, Secret Access Key, Region (e.g., us-east-1)
   ```

4. **Service Quotas** (verify these limits):
   - VPCs: 5 (default)
   - Elastic IPs: 5 (default)
   - NAT Gateways: 5 (default)
   - EKS Clusters: 100 (default)

### Domain Requirements

- **Registered domain name** (e.g., from Route53, Namecheap, or GoDaddy)
- **DNS management access** for creating A/CNAME records
- OR use **nip.io** for testing (no domain registration needed)

---

## Architecture Overview

### AWS Resources Created

```
┌─────────────────────────────────────────────────────┐
│                    AWS Account                       │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │         VPC (10.0.0.0/16)                      │ │
│  │                                                 │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────┐│ │
│  │  │ AZ us-east-1a│  │ AZ us-east-1b│  │AZ 1c    ││ │
│  │  │             │  │             │  │         ││ │
│  │  │ Public      │  │ Public      │  │ Public  ││ │
│  │  │ 10.0.1.0/24 │  │ 10.0.2.0/24 │  │10.0.3/24││ │
│  │  │             │  │             │  │         ││ │
│  │  │ Private     │  │ Private     │  │ Private ││ │
│  │  │ 10.0.11.0/24│  │ 10.0.12.0/24│  │10.0.13/ ││ │
│  │  └─────────────┘  └─────────────┘  └─────────┘│ │
│  │                                                 │ │
│  │  Internet Gateway ←→ NAT Gateway               │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │         EKS Cluster (cmbcluster-eks)           │ │
│  │  - 2 x t3.medium nodes (autoscaling 1-3)      │ │
│  │  - AWS Load Balancer Controller                │ │
│  │  - cert-manager (Let's Encrypt)                │ │
│  │  - S3 CSI Driver (Mountpoint)                  │ │
│  │  - EBS CSI Driver                              │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │         Amazon S3                              │ │
│  │  - cmbcluster-eks-db-{account-id}             │ │
│  │  - cmbcluster-eks-user-* (per-user buckets)   │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │         Amazon ECR                             │ │
│  │  - cmbcluster-eks-backend                      │ │
│  │  - cmbcluster-eks-frontend                     │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │         AWS Cognito (Optional)                 │ │
│  │  - User Pool: cmbcluster-users                 │ │
│  │  - App Client with OAuth 2.0                   │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Resource Naming Convention

| Resource | Format | Example |
|----------|--------|---------|
| VPC | `{cluster}-vpc` | `cmbcluster-eks-vpc` |
| EKS Cluster | `{cluster}` | `cmbcluster-eks` |
| S3 Buckets | `{cluster}-{type}-{account}` | `cmbcluster-eks-db-123456789012` |
| ECR Repos | `{cluster}-{service}` | `cmbcluster-eks-backend` |
| IAM Roles | `{cluster}-{role}-role` | `cmbcluster-eks-workload-role` |

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

Edit `.env` with your AWS configuration:

```bash
# === CLOUD PROVIDER SELECTION ===
CLOUD_PROVIDER=aws

# === AWS INFRASTRUCTURE ===
AWS_ACCOUNT_ID=123456789012  # Your AWS account ID
AWS_REGION=us-east-1
EKS_CLUSTER_NAME=cmbcluster-eks
ECR_REGISTRY_URL=123456789012.dkr.ecr.us-east-1.amazonaws.com

# === NETWORKING & DNS ===
DOMAIN=app.example.com  # Your domain
API_URL=https://api.app.example.com
FRONTEND_URL=https://app.example.com

# === SSL & AUTHENTICATION ===
LETSENCRYPT_EMAIL=your-email@example.com

# === AUTHENTICATION PROVIDER ===
AUTH_PROVIDER=auto  # or "cognito" or "google"

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

### Step 3: Set Up AWS Infrastructure

Run the AWS cluster setup script:

```bash
./scripts/aws/setup-cluster.sh
```

This script will:
1. ✅ Create VPC with 3 availability zones
2. ✅ Create Internet Gateway and NAT Gateway
3. ✅ Create EKS cluster
4. ✅ Create node group (t3.medium, 2 nodes)
5. ✅ Install AWS Load Balancer Controller
6. ✅ Install cert-manager
7. ✅ Install S3 CSI Driver (Mountpoint)
8. ✅ Install EBS CSI Driver
9. ✅ Create ECR repositories
10. ✅ Create S3 buckets
11. ✅ Configure IAM roles (IRSA)

**Duration**: 20-30 minutes

**Verify cluster is ready**:

```bash
kubectl get nodes
# Should show 2 nodes in Ready state

kubectl get pods -A
# Should show all system pods running
```

### Step 4: Configure Authentication

You have two options:

#### Option A: AWS Cognito (Recommended for AWS)

Run the Cognito setup script:

```bash
./scripts/aws/setup-cognito.sh
```

This creates:
- Cognito User Pool
- App Client with OAuth 2.0
- Configuration file: `cognito-config-{pool-id}.env`

**Update your `.env` with the output**:

```bash
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_CLIENT_ID=abc123xyz456
COGNITO_CLIENT_SECRET=your-secret-here
COGNITO_ISSUER=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX
```

#### Option B: Google OAuth (Deployment-Agnostic)

1. Go to [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials
2. Create OAuth 2.0 Client ID (Web application)
3. Add authorized redirect URIs:
   - `https://YOUR_DOMAIN/api/auth/callback/google`
   - `http://localhost:3000/api/auth/callback/google` (for testing)

4. Update `.env`:

```bash
AUTH_PROVIDER=google
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret-here
```

### Step 5: Build and Push Docker Images

Build images and push to ECR:

```bash
./scripts/aws/build-images.sh
```

This will:
1. Authenticate with ECR
2. Build backend Docker image
3. Build frontend Docker image
4. Push images to ECR

**Duration**: 5-10 minutes

### Step 6: Deploy Application

Deploy CMBCluster to EKS:

```bash
./scripts/aws/deploy.sh
```

This will:
1. Validate configuration
2. Create Kubernetes secrets
3. Deploy using Helm
4. Wait for pods to be ready
5. Display load balancer DNS

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

#### Option A: Using Route53 (Recommended)

1. Get the load balancer DNS name:

```bash
kubectl get ingress -n cmbcluster -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}'
```

2. Create Route53 records:

**For the frontend**:
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "app.example.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "k8s-cmbclust-xxxx.us-east-1.elb.amazonaws.com"}]
      }
    }]
  }'
```

**For the API**:
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.app.example.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "k8s-cmbclust-xxxx.us-east-1.elb.amazonaws.com"}]
      }
    }]
  }'
```

#### Option B: Using nip.io (Testing Only)

1. Get the load balancer IP:

```bash
# Note: AWS ELBs use DNS names, not IPs. Use the DNS name directly.
LB_DNS=$(kubectl get ingress -n cmbcluster -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}')
echo $LB_DNS
```

2. Update `.env`:

```bash
# For testing with nip.io, you'd typically need the IP, but AWS uses DNS names
# Instead, use the full DNS name for testing
DOMAIN=${LB_DNS}
API_URL=https://${LB_DNS}
FRONTEND_URL=https://${LB_DNS}
```

3. Redeploy:

```bash
./scripts/aws/deploy.sh
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

### Cognito Configuration Details

After running `setup-cognito.sh`, you should have:

**User Pool Settings**:
- Password policy: Min 8 characters, requires uppercase, lowercase, numbers
- Email verification: Required
- MFA: Optional (can be enabled)
- Account recovery: Email-based

**OAuth 2.0 Settings**:
- Flows: Authorization code grant
- Scopes: openid, email, profile
- Callback URLs: Configured for your domain

**First User Setup**:

1. Visit your application: `https://app.example.com`
2. Click "Sign in with Cognito"
3. Sign up with email
4. Verify email (check inbox)
5. Sign in - **first user becomes admin automatically**

### Google OAuth Configuration Details

**Authorized JavaScript Origins**:
- `https://app.example.com`

**Authorized Redirect URIs**:
- `https://app.example.com/api/auth/callback/google`

**First User Setup**:

1. Visit your application: `https://app.example.com`
2. Click "Sign in with Google"
3. Authorize application
4. Sign in - **first user becomes admin automatically**

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
4. Verify S3 bucket was created:

```bash
aws s3 ls | grep cmbcluster-eks-user
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
# {"status": "healthy", "cloud_provider": "aws"}

# Frontend health
curl https://app.example.com/

# Should return HTML
```

### S3 Access Test

```bash
# Backend pods should be able to access S3
kubectl exec -n cmbcluster deployment/cmbcluster-backend -- aws s3 ls

# Should list buckets
```

### IRSA Verification

```bash
# Check service account annotation
kubectl get sa cmbcluster-ksa -n cmbcluster -o yaml

# Should show: eks.amazonaws.com/role-arn annotation
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
1. **Insufficient resources**: Scale up node group
2. **Image pull errors**: Check ECR authentication
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
```

### Issue: Authentication Failing

**Symptoms**: "Invalid token" or "No authentication provider configured"

**Diagnosis**:
```bash
# Check backend logs
kubectl logs -n cmbcluster deployment/cmbcluster-backend | grep -i auth

# Check environment variables
kubectl exec -n cmbcluster deployment/cmbcluster-backend -- env | grep COGNITO
kubectl exec -n cmbcluster deployment/cmbcluster-backend -- env | grep GOOGLE
```

**Common Causes**:
1. **Missing credentials**: Cognito/Google credentials not set
2. **Incorrect issuer URL**: Cognito issuer doesn't match region/pool
3. **Callback URL mismatch**: Redirect URI not configured in Cognito/Google

**Solutions**:
```bash
# Verify configuration
kubectl get configmap -n cmbcluster cmbcluster-backend -o yaml

# Update secrets
kubectl delete secret cmbcluster-backend-secret -n cmbcluster
./scripts/aws/deploy.sh --skip-build
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
1. **DNS not propagated**: Domain doesn't point to load balancer
2. **HTTP-01 challenge failing**: Load balancer not routing to cert-manager
3. **Rate limiting**: Let's Encrypt rate limit hit

**Solutions**:
```bash
# Check DNS resolution
nslookup app.example.com

# Check ingress configuration
kubectl get ingress -n cmbcluster -o yaml

# Delete and recreate certificate
kubectl delete certificate -n cmbcluster --all
kubectl delete certificaterequest -n cmbcluster --all
# Wait for automatic recreation
```

### Issue: S3 Buckets Not Mounting

**Symptoms**: User environments fail to create, "failed to mount S3 bucket" error

**Diagnosis**:
```bash
# Check S3 CSI driver
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-mountpoint-s3-csi-driver

# Check user pod logs
kubectl logs -n cmbcluster POD_NAME
```

**Common Causes**:
1. **S3 CSI driver not installed**: Missing from cluster setup
2. **IRSA not configured**: Pod can't access S3
3. **Bucket doesn't exist**: Check S3 console

**Solutions**:
```bash
# Reinstall S3 CSI driver
kubectl apply -k "github.com/awslabs/mountpoint-s3-csi-driver/deploy/kubernetes/overlays/stable/?ref=v1.5.0"

# Verify IRSA role
aws iam get-role --role-name cmbcluster-eks-workload-role

# Check bucket access
aws s3 ls --profile your-profile
```

### Issue: Load Balancer Not Creating

**Symptoms**: Ingress has no ADDRESS field

**Diagnosis**:
```bash
kubectl describe ingress -n cmbcluster
kubectl logs -n kube-system deployment/aws-load-balancer-controller
```

**Common Causes**:
1. **ALB Controller not installed**: Missing from setup
2. **IAM permissions**: ALB controller can't create load balancers
3. **Subnet tags missing**: Private subnets not tagged correctly

**Solutions**:
```bash
# Check ALB controller
kubectl get deployment -n kube-system aws-load-balancer-controller

# Check subnet tags
aws ec2 describe-subnets --filters "Name=vpc-id,Values=YOUR_VPC_ID" \
  --query 'Subnets[*].[SubnetId,Tags]'

# Should have: kubernetes.io/role/internal-elb = 1
```

---

## Cost Optimization

### Development Environment

**Estimated Cost**: $100-150/month

**Resources**:
- EKS Control Plane: $73/month
- EC2 Instances (2 x t3.medium): $60/month
- NAT Gateway: $32/month
- S3 Storage (100GB): $2.30/month
- Data Transfer: $10/month

**Optimization Tips**:
1. **Use single NAT Gateway** (already configured)
2. **Autoscaling**: Scale down to 1 node during off-hours
3. **Spot Instances**: Use for dev/staging
4. **S3 Lifecycle Policies**: Move old data to Glacier

### Production Environment

**Estimated Cost**: $300-500/month

**Resources**:
- EKS Control Plane: $73/month
- EC2 Instances (3 x t3.large): $180/month
- NAT Gateways (3 AZs): $96/month
- S3 Storage (1TB): $23/month
- ALB: $22/month
- Data Transfer: $50/month

**Optimization Tips**:
1. **Reserved Instances**: 30-40% savings for stable workloads
2. **Savings Plans**: Flexible commitment-based discounts
3. **S3 Intelligent-Tiering**: Automatic cost optimization
4. **CloudWatch Logs retention**: Set to 7-30 days

### Cost Monitoring

```bash
# Enable AWS Cost Explorer
# Set up billing alerts in AWS Console

# Tag resources for cost tracking
aws resourcegroupstaggingapi tag-resources \
  --resource-arn-list "arn:aws:eks:..." \
  --tags Project=CMBCluster,Environment=Production
```

---

## Security Hardening

### Production Security Checklist

#### Infrastructure Level

- [ ] **VPC**: Private subnets for worker nodes
- [ ] **Security Groups**: Minimal ingress rules
- [ ] **IAM**: Use IRSA, no long-term credentials
- [ ] **S3 Buckets**: Enable versioning and encryption
- [ ] **ECR**: Enable image scanning
- [ ] **CloudTrail**: Enable logging for audit
- [ ] **VPC Flow Logs**: Enable for network monitoring

#### Kubernetes Level

- [ ] **Network Policies**: Restrict pod-to-pod communication
- [ ] **Pod Security Standards**: Enforce restricted policies
- [ ] **RBAC**: Minimal permissions per service account
- [ ] **Secrets**: Use AWS Secrets Manager or Parameter Store
- [ ] **Image Pull Policies**: Always use `IfNotPresent`
- [ ] **Resource Limits**: Set CPU/memory limits

#### Application Level

- [ ] **TLS**: Enforce HTTPS with strong ciphers
- [ ] **Authentication**: MFA enabled for Cognito
- [ ] **Rate Limiting**: Enable in backend configuration
- [ ] **Security Headers**: CSP, HSTS, X-Frame-Options
- [ ] **Session Management**: Secure cookies, short expiry
- [ ] **Logging**: Centralized logging to CloudWatch

### Enable AWS Security Services

```bash
# Enable GuardDuty (threat detection)
aws guardduty create-detector --enable

# Enable Security Hub
aws securityhub enable-security-hub

# Enable Config (compliance monitoring)
aws configservice put-configuration-recorder ...

# Enable CloudTrail
aws cloudtrail create-trail --name cmbcluster-trail \
  --s3-bucket-name cmbcluster-cloudtrail
```

### Regular Security Tasks

**Weekly**:
- Review CloudWatch logs for anomalies
- Check AWS Security Hub findings

**Monthly**:
- Rotate secrets (Cognito client secrets, API keys)
- Review IAM permissions
- Update container images

**Quarterly**:
- Security audit
- Penetration testing
- Disaster recovery drill

---

## Next Steps

After successful deployment:

1. **Set Up Monitoring**:
   - Configure CloudWatch dashboards
   - Set up alerts for critical metrics
   - Enable container insights

2. **Configure Backups**:
   - S3 bucket versioning (already enabled)
   - Automated snapshots
   - Disaster recovery plan

3. **Performance Tuning**:
   - Monitor pod resource usage
   - Adjust node instance types
   - Configure autoscaling policies

4. **Documentation**:
   - Document your specific configuration
   - Create runbooks for common operations
   - Train team on deployment process

---

## Support & Resources

### Official Documentation

- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Amazon S3 Documentation](https://docs.aws.amazon.com/s3/)
- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [Mountpoint for S3](https://github.com/awslabs/mountpoint-s3)

### CMBCluster Resources

- [Main README](../README.md)
- [Polycloud Architecture](./ARCHITECTURE_POLYCLOUD.md)
- [GCP Deployment Guide](./DEPLOYMENT_GCP.md)
- [GitHub Issues](https://github.com/yourusername/cmbcluster/issues)

### Community

- GitHub Discussions
- Slack Channel (if available)
- Stack Overflow: Tag `cmbcluster`

---

**Document Version**: 1.0
**Last Updated**: 2025-10-24
**Maintainer**: CMBCluster Team
