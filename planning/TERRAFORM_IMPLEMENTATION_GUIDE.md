# CMBCluster Terraform Implementation Guide

**Status:** ✅ Complete Terraform Infrastructure as Code
**Last Updated:** 2025-10-24
**Supports:** AWS & GCP Multi-Cloud Deployments

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Getting Started](#getting-started)
5. [Module Documentation](#module-documentation)
6. [Deployment Workflows](#deployment-workflows)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Terraform implementation provides **Infrastructure as Code** for deploying CMBCluster across AWS and GCP. It includes:

✅ **Complete Infrastructure Management**
- VPC with Multi-AZ networking
- EKS/GKE cluster setup
- Container registries (ECR/Artifact Registry)
- Storage (S3/GCS)
- IAM/Workload Identity configuration
- Cognito/OAuth setup

✅ **Production-Ready**
- State management (remote backend support)
- Automatic dependency management
- Parallel resource creation
- Cost optimization
- Security best practices

✅ **Deployment-Agnostic**
- Single configuration for both AWS and GCP
- Variable-driven cloud selection
- Automatic provider detection

---

## Architecture

```
terraform/
├── main.tf                              # Root configuration
├── variables.tf                         # Input variables
├── outputs.tf                           # Output values
├── terraform.tfvars.example             # Example configuration
│
├── modules/
│   ├── aws/
│   │   ├── vpc/                         # VPC, subnets, NAT, IGW
│   │   ├── eks/                         # EKS cluster, node groups
│   │   ├── ecr/                         # ECR repositories
│   │   ├── s3/                          # S3 buckets
│   │   ├── iam/                         # IAM roles, IRSA
│   │   └── cognito/                     # Cognito user pool
│   │
│   ├── gcp/
│   │   ├── gke/                         # GKE cluster
│   │   ├── network/                     # VPC, subnets
│   │   ├── storage/                     # GCS buckets
│   │   ├── artifact-registry/           # Container registry
│   │   └── iam/                         # Service accounts, roles
│   │
│   └── kubernetes/
│       ├── namespaces/                  # Kubernetes namespace
│       ├── helm/                        # Helm chart deployment
│       ├── csi-drivers/                 # Storage drivers
│       ├── cert-manager/                # TLS management
│       └── aws-load-balancer-controller/ # ALB controller
│
└── environments/
    ├── dev.tfvars                       # Development config
    ├── staging.tfvars                   # Staging config
    └── prod.tfvars                      # Production config
```

---

## Prerequisites

### Required Tools

```bash
# Terraform >= 1.5.0
terraform version

# AWS CLI v2
aws --version

# Google Cloud CLI
gcloud --version

# kubectl
kubectl version --client

# Helm 3
helm version

# For state management
# AWS S3 + DynamoDB (AWS)
# Google Cloud Storage (GCP)
```

### AWS Prerequisites

1. **AWS Account**
   - Account ID
   - Appropriate IAM permissions
   - Valid credentials configured

2. **IAM Permissions**
   - EC2, EKS, VPC, S3, ECR, IAM, Cognito
   - Or use `AdministratorAccess` for initial setup

3. **Domain (Optional)**
   - For LoadBalancer/Ingress DNS
   - Can use nip.io for development

### GCP Prerequisites

1. **GCP Project**
   - Project ID
   - Billing enabled
   - APIs enabled: GKE, Artifact Registry, GCS, IAM

2. **GCP Permissions**
   - Kubernetes Engine Admin
   - Compute Admin
   - Service Account Admin
   - Storage Admin

3. **Service Account**
   - Created with appropriate roles
   - Key file (optional)

---

## Getting Started

### 1. Initialize Terraform

```bash
# Clone or navigate to terraform directory
cd terraform

# Initialize Terraform (downloads providers)
terraform init

# Option: Configure remote backend (S3/GCS)
# See "Remote State Management" section below
```

### 2. Configure Variables

**Option A: Using tfvars file**
```bash
# Copy example configuration
cp environments/dev.tfvars terraform.tfvars

# Edit for your environment
editor terraform.tfvars
```

**Option B: Environment variables**
```bash
export TF_VAR_cloud_provider="aws"
export TF_VAR_aws_region="us-east-1"
export TF_VAR_cluster_name="cmbcluster"
# ... other variables
```

### 3. Validate Configuration

```bash
# Validate Terraform syntax
terraform validate

# Format code
terraform fmt

# Lint (optional, requires tflint)
tflint
```

### 4. Plan Deployment

```bash
# Show what will be created
terraform plan -out=tfplan

# Review the plan carefully
# Look for:
# - Resource creation order
# - Parallel operations
# - Dependencies
```

### 5. Apply Configuration

```bash
# Apply the plan
terraform apply tfplan

# Or apply directly (without saved plan)
terraform apply

# Terraform will prompt for confirmation
```

### 6. Get Outputs

```bash
# Display all outputs
terraform output

# Get specific output
terraform output aws_eks_cluster_name

# Get raw output (no formatting)
terraform output -raw kubeconfig_command
```

---

## Module Documentation

### AWS VPC Module

**Location:** `modules/aws/vpc`

**Creates:**
- VPC with custom CIDR
- Multi-AZ public subnets
- Multi-AZ private subnets
- Internet Gateway
- NAT Gateway (with Elastic IP)
- Route tables (public & private)
- VPC Flow Logs (CloudWatch)
- VPC Endpoints (S3, ECR, Logs)
- Security groups

**Variables:**
```hcl
cluster_name       = "cmbcluster"
region            = "us-east-1"
vpc_cidr          = "10.0.0.0/16"
public_subnets    = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
private_subnets   = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
```

**Outputs:**
```
vpc_id
vpc_cidr
public_subnet_ids
private_subnet_ids
nat_gateway_id
nat_gateway_eip
```

### AWS EKS Module

**Location:** `modules/aws/eks`

**Creates:**
- EKS cluster (with public/private endpoints)
- Node group with auto-scaling
- IAM roles for EKS
- OIDC provider for IRSA
- CloudWatch logging

**Variables:**
```hcl
cluster_name           = "cmbcluster"
vpc_id                = aws_vpc.main.id
subnet_ids            = [private subnets]
kubernetes_version    = "1.28"
node_group_min_size   = 1
node_group_max_size   = 3
node_instance_type    = "t3.medium"
```

**Outputs:**
```
cluster_name
cluster_endpoint
cluster_arn
cluster_ca_certificate
oidc_provider_arn
```

### AWS IAM Module

**Location:** `modules/aws/iam`

**Creates:**
- IRSA (IAM Roles for Service Accounts)
- S3 access policies
- ECR access policies
- ALB controller role
- Cognito integration roles

**Features:**
- Least privilege policies
- Automatic OIDC trust setup
- Role tagging

### Kubernetes Helm Module

**Location:** `modules/kubernetes/helm`

**Deploys:**
- cmbcluster backend
- cmbcluster frontend
- Ingress configuration
- Services
- ConfigMaps & Secrets
- Volumes (for storage)

**Environment Variables Passed:**
```
CLOUD_PROVIDER
AWS_REGION / GCP_REGION
AUTH_PROVIDER
GOOGLE_CLIENT_ID
COGNITO_USER_POOL_ID
And more...
```

---

## Deployment Workflows

### AWS Deployment

```bash
# 1. Set variables
cat > terraform.tfvars << EOF
cloud_provider = "aws"
environment    = "dev"
cluster_name   = "cmbcluster"
aws_region     = "us-east-1"
domain         = "cmbcluster.example.com"
letsencrypt_email = "admin@example.com"

# Auth
google_client_id     = "your-google-client-id"
google_client_secret = "your-google-client-secret"

# Secrets
secret_key      = "$(openssl rand -base64 32)"
nextauth_secret = "$(openssl rand -base64 32)"
EOF

# 2. Initialize
terraform init

# 3. Plan
terraform plan -out=aws.tfplan

# 4. Review plan
# Check resource creation order
# Verify cloud resources
# Check for errors

# 5. Apply
terraform apply aws.tfplan

# 6. Get outputs
terraform output kubeconfig_command
terraform output application_backend_url

# 7. Configure kubectl
eval "$(terraform output -raw kubeconfig_command)"

# 8. Verify cluster
kubectl get nodes
kubectl get pods -n cmbcluster

# 9. Copy environment
terraform output -raw env_file_content >> ../.env

# 10. Deploy images
aws ecr get-login-password | docker login --username AWS --password-stdin $(terraform output -raw aws_ecr_registry_url)
docker push $(terraform output -raw aws_ecr_registry_url)/backend:latest
docker push $(terraform output -raw aws_ecr_registry_url)/frontend:latest
```

### GCP Deployment

```bash
# 1. Set variables
cat > terraform.tfvars << EOF
cloud_provider  = "gcp"
environment     = "dev"
cluster_name    = "cmbcluster"
gcp_project_id  = "your-project-id"
gcp_region      = "us-central1"
letsencrypt_email = "admin@example.com"

# Auth
auth_provider       = "google"
google_client_id    = "your-google-client-id"
google_client_secret = "your-google-client-secret"

# Secrets
secret_key      = "$(openssl rand -base64 32)"
nextauth_secret = "$(openssl rand -base64 32)"
EOF

# 2. Initialize
terraform init

# 3. Plan
terraform plan -out=gcp.tfplan

# 4. Apply
terraform apply gcp.tfplan

# 5. Configure kubectl
eval "$(terraform output -raw kubeconfig_command)"

# 6. Verify
kubectl get nodes

# 7. Prepare images
gcloud auth configure-docker
docker push $(terraform output -raw gcp_artifact_registry)/backend:latest
docker push $(terraform output -raw gcp_artifact_registry)/frontend:latest
```

---

## Remote State Management

### AWS S3 Backend

```hcl
# terraform/backend.tf
terraform {
  backend "s3" {
    bucket         = "cmbcluster-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

**Setup:**
```bash
# Create S3 bucket
aws s3api create-bucket \
  --bucket cmbcluster-terraform-state \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket cmbcluster-terraform-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket cmbcluster-terraform-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Create DynamoDB table for locks
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1
```

### GCP Cloud Storage Backend

```hcl
# terraform/backend.tf
terraform {
  backend "gcs" {
    bucket  = "cmbcluster-terraform-state"
    prefix  = "terraform/state"
  }
}
```

**Setup:**
```bash
# Create bucket
gsutil mb -p your-project-id gs://cmbcluster-terraform-state

# Enable versioning
gsutil versioning set on gs://cmbcluster-terraform-state

# Enable uniform bucket-level access
gsutil uniformbucketlevelaccess set on gs://cmbcluster-terraform-state
```

---

## Parallel Resource Creation

Terraform automatically parallelizes resource creation where there are no dependencies:

```
Phase 1 (Parallel):
  - VPC
  - IAM roles
  - S3 buckets
  ├─ 5-10 minutes

Phase 2 (Parallel, waits for Phase 1):
  - EKS cluster (uses VPC)
  - ECR repositories (uses IAM)
  ├─ 15-20 minutes

Phase 3 (Waits for Phase 2):
  - Node group (uses EKS cluster)
  ├─ 10-15 minutes

Phase 4 (Parallel, waits for Phases 1-3):
  - Kubernetes namespaces
  - CSI drivers
  - Helm deployment (uses EKS)
  ├─ 5-10 minutes

**Total Time: 35-50 minutes**
```

**Adjust parallelism:**
```bash
terraform apply -parallelism=10  # Default is 10
terraform apply -parallelism=20  # Increase for faster deployment
```

---

## Cost Optimization

### Development Environment

```hcl
# terraform/environments/dev.tfvars

# Minimal resources
aws_node_group_min_size = 1
aws_node_group_max_size = 3
aws_node_instance_type  = "t3.medium"

# Single NAT Gateway (acceptable for dev)
# Single replica per service
```

**Estimated Cost (AWS):** $150-250/month

### Production Environment

```hcl
# terraform/environments/prod.tfvars

# High availability
aws_node_group_min_size = 3
aws_node_group_max_size = 10
aws_node_instance_type  = "t3.large"

# NAT per AZ (HA)
# Multiple replicas
# Backup/snapshots
```

**Estimated Cost (AWS):** $500-1000/month

---

## Best Practices

### 1. Use Remote State

```bash
# Store state in S3/GCS with encryption and locking
# Prevents accidental local state loss
terraform init -backend-config="bucket=your-bucket"
```

### 2. Version Lock Providers

```hcl
# terraform/main.tf
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"  # Lock major version
    }
  }
}
```

### 3. Use Workspaces for Environments

```bash
# Create workspace for each environment
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Switch between workspaces
terraform workspace select dev
```

### 4. Always Run Plan First

```bash
# Never apply without reviewing plan
terraform plan -out=tfplan
# Review tfplan carefully
terraform apply tfplan
```

### 5. Use Input Variables

```bash
# Don't hardcode values
# Use tfvars for each environment
terraform apply -var-file="environments/prod.tfvars"
```

### 6. Tag Everything

```hcl
# Automatic tagging via default_tags
provider "aws" {
  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "Terraform"
    }
  }
}
```

### 7. Document Changes

```bash
# Use git to track tfvars changes
git add terraform.tfvars
git commit -m "Update prod cluster size"

# Use terraform plan for CI/CD
terraform plan | tee tfplan.txt
```

### 8. Implement Destruction Safeguards

```hcl
# Add lifecycle rules to prevent accidental deletion
lifecycle {
  prevent_destroy = true
}

# Or use -lock-timeout to prevent concurrent changes
terraform apply -lock-timeout=10m
```

---

## Troubleshooting

### Common Issues

#### Issue: "Error: Provider version not found"

```bash
# Solution: Update provider version
terraform init -upgrade

# Or specify correct version
terraform init -backend=false  # Skip backend
```

#### Issue: "Error: Resource creation timeout"

```bash
# Solution: Increase timeout
terraform apply -lock-timeout=30m

# Or check AWS/GCP service limits
# May need to request limit increase
```

#### Issue: "Error: IAM role not found"

```bash
# Solution: Ensure IAM permissions
aws iam list-roles

# Verify policies
aws iam list-role-policies --role-name RoleName
```

#### Issue: "Error: VPC endpoint creation failed"

```bash
# Solution: Check if service is available in region
aws ec2 describe-vpc-endpoint-services

# May need to use different region
```

### Debug Mode

```bash
# Enable debug logging
export TF_LOG=DEBUG
terraform apply 2>&1 | tee debug.log

# Disable logging
unset TF_LOG
```

### State Troubleshooting

```bash
# List all resources in state
terraform state list

# Show specific resource
terraform state show aws_eks_cluster.main

# Remove resource from state (CAREFUL!)
terraform state rm aws_eks_cluster.main

# Validate state
terraform state validate
```

---

## Next Steps

1. ✅ Review this guide
2. ⏳ Prepare `terraform.tfvars` for your environment
3. ⏳ Run `terraform init`
4. ⏳ Run `terraform plan` and review
5. ⏳ Run `terraform apply`
6. ⏳ Configure kubectl
7. ⏳ Deploy application images
8. ⏳ Verify deployment

---

## Integration with CI/CD

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  pull_request:
    paths: ['terraform/**']
  push:
    branches: ['main']

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.5.0

      - name: Plan
        run: terraform plan -out=tfplan

      - name: Apply (main branch only)
        if: github.ref == 'refs/heads/main'
        run: terraform apply tfplan
```

---

## Additional Resources

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/)
- [Terraform Kubernetes Provider](https://registry.terraform.io/providers/hashicorp/kubernetes/)
- [Terraform Best Practices](https://www.terraform.io/language/values/variables)

---

**Status:** ✅ **READY FOR PRODUCTION DEPLOYMENT**

All Terraform modules are complete, tested, and ready for immediate use. The infrastructure will deploy in parallel with full state management and cost optimization.

