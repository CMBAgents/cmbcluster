# CMBCluster AWS EKS Deployment Guide

This guide provides complete instructions for deploying CMBCluster on Amazon Web Services using EKS (Elastic Kubernetes Service).

---

## Prerequisites

Before beginning the deployment, ensure you have the following tools installed and configured:

### Required Tools

**AWS CLI**
```bash
aws --version
aws configure
```

**kubectl**
```bash
kubectl version --client
```

**eksctl**
```bash
eksctl version
```

**Helm**
```bash
helm version
```

### AWS Account Requirements

Your AWS account must have appropriate permissions for:
- EKS (Elastic Kubernetes Service)
- VPC (Virtual Private Cloud)
- IAM (Identity and Access Management)
- S3 (Simple Storage Service)
- ECR (Elastic Container Registry)

---

## Quick Start Guide

### Step 1: Configure Environment

Copy the AWS environment template:

```bash
cp .env.example.aws .env
```

Edit the `.env` file with your configuration values:

```bash
AWS_ACCOUNT_ID=your-account-id
AWS_REGION=us-east-1
CLUSTER_NAME=cmbcluster
BASE_DOMAIN=cmbcluster.yourdomain.com
GOOGLE_CLIENT_ID=your-oauth-client-id
GOOGLE_CLIENT_SECRET=your-oauth-secret
SECRET_KEY=$(openssl rand -base64 32)
LETSENCRYPT_EMAIL=your-email@example.com
```

### Step 2: Setup Infrastructure

Run the setup script (estimated time: 15-20 minutes):

```bash
./scripts/aws/setup-cluster.sh
```

This script creates the following resources:
- EKS cluster with VPC and subnets
- ECR repository for container images
- S3 buckets for storage
- IAM roles with IRSA (IAM Roles for Service Accounts)
- AWS Load Balancer Controller
- cert-manager for SSL certificates

### Step 3: Build and Push Container Images

Login to ECR:

```bash
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

Build Docker images:

```bash
docker build -t cmbcluster-backend:latest ./backend
docker build -t cmbcluster-frontend:latest ./frontend
docker build -t cmbcluster-user-env:latest ./user-environment
```

Tag and push images to ECR:

```bash
# Backend
docker tag cmbcluster-backend:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/cmbcluster-images/cmbcluster-backend:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/cmbcluster-images/cmbcluster-backend:latest

# Repeat for frontend and user-env images
```

### Step 4: Deploy Application

Deploy the application to your EKS cluster:

```bash
./scripts/aws/deploy.sh
```

### Step 5: Configure DNS

Get the Application Load Balancer DNS name:

```bash
kubectl get ingress -n cmbcluster
```

Create the following CNAME records in your DNS provider:
- `cmbcluster.yourdomain.com` → `<ALB-DNS-NAME>`
- `api.cmbcluster.yourdomain.com` → `<ALB-DNS-NAME>`
- `*.cmbcluster.yourdomain.com` → `<ALB-DNS-NAME>`

---

## AWS Service Mapping

Comparison of GCP services to AWS equivalents:

| GCP Service | AWS Equivalent |
|-------------|----------------|
| GKE | EKS |
| Cloud Storage | S3 |
| Artifact Registry | ECR |
| Load Balancer | ALB |
| Workload Identity | IRSA |

---

## Available Scripts

### setup-cluster.sh

Creates the complete AWS infrastructure for CMBCluster.

**Usage:**
```bash
./scripts/aws/setup-cluster.sh [CLUSTER_NAME] [AWS_REGION] [AWS_ACCOUNT_ID]
```

### deploy.sh

Deploys the CMBCluster application to your EKS cluster.

**Usage:**
```bash
./scripts/aws/deploy.sh [CLUSTER_NAME] [AWS_REGION] [BASE_DOMAIN]
```

### cleanup.sh

Removes all AWS resources created for CMBCluster. **USE WITH CAUTION** - this will delete all data.

**Usage:**
```bash
./scripts/aws/cleanup.sh [CLUSTER_NAME] [AWS_REGION]
```

---

## Troubleshooting

### Pods Not Starting

Check pod status and logs:

```bash
kubectl describe pod <pod-name> -n cmbcluster
kubectl logs <pod-name> -n cmbcluster
```

### IAM Role Issues

Verify the service account configuration:

```bash
kubectl describe sa cmbcluster-ksa -n cmbcluster
```

### Application Load Balancer Problems

Check the ALB controller logs:

```bash
kubectl logs -n kube-system deployment/aws-load-balancer-controller
```

---

## Cost Estimate

Approximate monthly costs for running CMBCluster on AWS:

| Service | Estimated Cost |
|---------|----------------|
| EKS Cluster | ~$73/month |
| EC2 Instances | ~$30-60/month |
| NAT Gateway | ~$32/month |
| Application Load Balancer | ~$16-20/month |
| Storage (S3, EBS) | Variable |
| **Total Estimated Cost** | **~$150-200/month** |

*Note: Actual costs may vary based on usage, region, and specific configuration choices.*

---

## Additional Support

For general CMBCluster documentation and support, please refer to the main README.md file in the project root directory.
