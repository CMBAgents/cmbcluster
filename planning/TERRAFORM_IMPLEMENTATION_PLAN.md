# CMBCluster Terraform Implementation Plan - Phased Approach

**Status:** 📋 **PLANNING PHASE**
**Date:** 2025-10-24
**Duration:** 3-4 weeks
**Team Size:** 1-2 engineers

---

## 📊 Executive Summary

This document outlines a **4-phase implementation plan** to replace existing shell scripts with Terraform infrastructure as code. The plan ensures:

✅ **Zero downtime** (parallel infrastructure)
✅ **Validation** at each phase
✅ **Team training** before cutover
✅ **Rollback capability** if needed
✅ **Audit trail** of all changes

---

## 🎯 Implementation Phases Overview

| Phase | Duration | Objective | Status |
|-------|----------|-----------|--------|
| **Phase 0** | Days 1-3 | Preparation & Environment Setup | 📋 Pending |
| **Phase 1** | Days 4-7 | Core AWS Infrastructure (VPC + EKS) | 📋 Pending |
| **Phase 2** | Days 8-11 | Storage & IAM (S3 + Cognito) | 📋 Pending |
| **Phase 3** | Days 12-15 | Kubernetes & Application Deployment | 📋 Pending |
| **Phase 4** | Days 16-21 | GCP Parity & Validation | 📋 Pending |
| **Phase 5** | Days 22-28 | Cutover & Shell Script Deprecation | 📋 Pending |

**Total Duration:** 4 weeks (21 business days)

---

## 📋 PHASE 0: Preparation & Environment Setup

**Duration:** Days 1-3
**Team:** 1 engineer + DevOps lead review
**Goal:** Prepare environment and baseline

### 0.1 Environment Preparation

#### 0.1.1 Infrastructure Account Setup
- [ ] **AWS Account Access**
  - [ ] Verify IAM permissions (AdministratorAccess or scoped)
  - [ ] Create IAM user for Terraform (service account)
  - [ ] Generate access keys
  - [ ] Configure AWS CLI: `aws configure`
  - [ ] Test access: `aws sts get-caller-identity`
  - **Deliverable:** AWS credentials configured locally

- [ ] **GCP Account Access**
  - [ ] Verify project access
  - [ ] Create service account for Terraform
  - [ ] Create service account key
  - [ ] Configure gcloud: `gcloud auth login`
  - [ ] Set default project: `gcloud config set project PROJECT_ID`
  - **Deliverable:** GCP credentials configured locally

#### 0.1.2 Tools Installation
- [ ] **Terraform**
  ```bash
  # macOS
  brew install terraform

  # Linux
  wget https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip
  unzip && sudo mv terraform /usr/local/bin/

  # Verify
  terraform version
  ```
  - **Required:** >= 1.5.0

- [ ] **kubectl**
  ```bash
  # macOS
  brew install kubectl

  # Linux
  curl -LO https://dl.k8s.io/release/v1.28.0/bin/linux/amd64/kubectl
  chmod +x kubectl && sudo mv kubectl /usr/local/bin/

  # Verify
  kubectl version --client
  ```

- [ ] **Helm**
  ```bash
  # macOS
  brew install helm

  # Linux
  curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

  # Verify
  helm version
  ```

- [ ] **AWS CLI v2**
  ```bash
  # macOS
  brew install awscli

  # Verify
  aws --version  # Should be 2.x.x
  ```

- [ ] **Google Cloud CLI**
  ```bash
  # Install gcloud
  curl https://sdk.cloud.google.com | bash

  # Verify
  gcloud --version
  ```

**Checkpoint 0.1:** All tools installed and verified
```bash
terraform version && kubectl version --client && helm version && aws --version && gcloud --version
```

### 0.2 Repository & Git Setup

#### 0.2.1 Git Configuration
- [ ] **Create feature branch**
  ```bash
  git checkout -b feature/terraform-implementation
  git pull origin main
  ```

- [ ] **Commit initial Terraform files**
  ```bash
  git add terraform/
  git commit -m "Add Terraform infrastructure code (Phase 0 commit)"
  git push origin feature/terraform-implementation
  ```

- [ ] **Create GitHub branch protection** (if applicable)
  - [ ] Require code review before merge
  - [ ] Require status checks
  - [ ] Require branch to be up-to-date

#### 0.2.2 Documentation Preparation
- [ ] **Copy implementation guide**
  - [ ] TERRAFORM_IMPLEMENTATION_GUIDE.md ✅
  - [ ] TERRAFORM_VS_SHELL_SCRIPTS.md ✅
  - [ ] TERRAFORM_SUMMARY.md ✅

- [ ] **Create implementation runbook**
  ```bash
  mkdir -p docs/terraform-implementation
  cp TERRAFORM_IMPLEMENTATION_GUIDE.md docs/terraform-implementation/
  ```

**Checkpoint 0.2:** Git branch ready with all Terraform code

### 0.3 State Management Setup

#### 0.3.1 Create S3 Backend (AWS)
```bash
# Create S3 bucket
aws s3api create-bucket \
  --bucket cmbcluster-terraform-state-aws \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket cmbcluster-terraform-state-aws \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket cmbcluster-terraform-state-aws \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket cmbcluster-terraform-state-aws \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1
```

**Deliverable:** S3 bucket + DynamoDB table for state

#### 0.3.2 Create GCS Backend (GCP)
```bash
# Create GCS bucket
gsutil mb -p your-project-id gs://cmbcluster-terraform-state-gcp

# Enable versioning
gsutil versioning set on gs://cmbcluster-terraform-state-gcp

# Enable uniform bucket-level access
gsutil uniformbucketlevelaccess set on gs://cmbcluster-terraform-state-gcp

# Set lifecycle (delete old versions after 30 days)
cat > lifecycle.json << 'EOF'
{
  "lifecycle": {
    "delete": {
      "num_newer_versions": 10
    }
  }
}
EOF
gsutil lifecycle set lifecycle.json gs://cmbcluster-terraform-state-gcp
```

**Deliverable:** GCS bucket for state

**Checkpoint 0.3:** State backends created and tested

### 0.4 Local Development Setup

#### 0.4.1 Terraform Configuration
```bash
cd terraform

# Create local terraform config
cat > terraform/backend-local.tf << 'EOF'
# Local backend for development
# Will migrate to S3/GCS in production
terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}
EOF

# Initialize Terraform (local backend for now)
terraform init
```

#### 0.4.2 Create Development Variables File
```bash
# Copy and customize for development
cp terraform/environments/dev.tfvars terraform/dev.local.tfvars

# Edit with local values
cat >> terraform/dev.local.tfvars << 'EOF'
# Development Overrides
cloud_provider       = "aws"
environment          = "dev"
cluster_name         = "cmbcluster-dev"
aws_region           = "us-east-1"
deployment_timestamp = "2025-10-24"
EOF
```

#### 0.4.3 Validate Terraform
```bash
cd terraform

# Validate syntax
terraform validate
# ✅ Success: Success! The configuration is valid.

# Format code
terraform fmt -recursive

# Optional: Lint with tflint
tflint --init && tflint
```

**Checkpoint 0.4:** Terraform initialized and validated

### 0.5 Team Training & Documentation

#### 0.5.1 Documentation Review
- [ ] **Engineer reads and understands:**
  - [ ] TERRAFORM_IMPLEMENTATION_GUIDE.md (30 min)
  - [ ] TERRAFORM_VS_SHELL_SCRIPTS.md (20 min)
  - [ ] Terraform module structure (15 min)
  - [ ] State management concepts (15 min)

- [ ] **Create internal wiki/docs**
  - [ ] Link to Terraform documentation
  - [ ] Team-specific configuration notes
  - [ ] Emergency procedures

#### 0.5.2 Team Walkthrough
- [ ] **DevOps Lead presents:**
  - [ ] Architecture overview (30 min)
  - [ ] Module breakdown (30 min)
  - [ ] Deployment workflow (20 min)
  - [ ] Rollback procedures (15 min)

- [ ] **Q&A Session**
  - [ ] Open discussion
  - [ ] Answer concerns
  - [ ] Document FAQs

**Checkpoint 0.5:** Team trained and ready

---

## 🔨 PHASE 1: Core AWS Infrastructure (VPC + EKS)

**Duration:** Days 4-7
**Team:** 1 engineer (with DevOps review)
**Goal:** Deploy VPC and EKS cluster

### 1.1 VPC Module Deployment

#### 1.1.1 Plan VPC Resources
```bash
cd terraform

# Create plan file for VPC
terraform plan \
  -target=module.aws_vpc \
  -var-file=dev.local.tfvars \
  -out=vpc.tfplan

# Review plan
terraform show vpc.tfplan
```

**Expected Resources:**
- 1 VPC (10.0.0.0/16)
- 3 Public subnets (10.0.1-3.0/24)
- 3 Private subnets (10.0.11-13.0/24)
- 1 Internet Gateway
- 1 NAT Gateway (+ Elastic IP)
- 2 Route Tables (public + private)
- Security groups
- VPC Flow Logs
- VPC Endpoints (S3, ECR, Logs)

#### 1.1.2 Apply VPC Configuration
```bash
# Review plan one more time
terraform show vpc.tfplan | less

# Apply VPC resources (takes ~5 minutes)
terraform apply vpc.tfplan

# Verify resources
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=cmbcluster-dev-vpc"
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-xxxxx"
```

**Checkpoint 1.1.1:** VPC successfully created

#### 1.1.3 Validate Network
```bash
# Get VPC details
terraform output aws_vpc_id
terraform output aws_private_subnet_ids
terraform output aws_public_subnet_ids

# Verify NAT Gateway is operational
aws ec2 describe-nat-gateways --filters "Name=tag:Name,Values=cmbcluster-dev-nat-gw"

# Verify route tables
aws ec2 describe-route-tables --filters "Name=tag:Name,Values=cmbcluster-dev-public-rt"
aws ec2 describe-route-tables --filters "Name=tag:Name,Values=cmbcluster-dev-private-rt"
```

**Checkpoint 1.1.2:** Network validated

### 1.2 EKS Cluster Deployment

#### 1.2.1 Plan EKS Resources
```bash
# Create plan for EKS cluster
terraform plan \
  -target=module.aws_eks \
  -var-file=dev.local.tfvars \
  -out=eks.tfplan

# Show what will be created
terraform show eks.tfplan
```

**Expected Resources:**
- 1 EKS cluster (kubernetes 1.28)
- 1 Node group (1-3 nodes, t3.medium)
- IAM roles for EKS
- OIDC provider for IRSA
- CloudWatch log group
- Security groups

#### 1.2.2 Apply EKS Configuration
```bash
# Apply EKS (takes ~15-20 minutes)
terraform apply eks.tfplan

# Watch progress
watch "aws eks describe-cluster --name cmbcluster-dev --query 'cluster.status'"

# Verify cluster is active (wait for status = ACTIVE)
aws eks describe-cluster --name cmbcluster-dev \
  --query 'cluster.[name,status,endpoint]' \
  --output table
```

**Checkpoint 1.2.1:** EKS cluster created

#### 1.2.3 Configure kubectl Access
```bash
# Get kubeconfig command from Terraform
eval "$(terraform output -raw kubeconfig_command)"

# Verify kubectl access
kubectl cluster-info
kubectl get nodes

# Expected: 1-2 nodes in NotReady state (wait for Ready)
watch kubectl get nodes

# Wait for nodes to be Ready (3-5 minutes)
```

**Checkpoint 1.2.2:** kubectl access verified

#### 1.2.4 Validate OIDC Provider
```bash
# Verify OIDC provider created (needed for IRSA)
aws iam list-open-id-connect-providers

# Check OIDC provider thumbprint
aws iam get-open-id-connect-provider \
  --open-id-connect-provider-arn $(terraform output -raw aws_oidc_provider_arn)
```

**Checkpoint 1.2.3:** OIDC provider verified

### 1.3 Testing & Validation

#### 1.3.1 Cluster Health Check
```bash
# Check cluster status
kubectl cluster-info
kubectl get nodes -o wide
kubectl get pods --all-namespaces

# Check node capacity
kubectl describe nodes | grep -A 5 "Allocatable"

# Check system pods
kubectl get pods -n kube-system
```

#### 1.3.2 Terraform State Validation
```bash
# Verify state has all resources
terraform state list | grep aws_eks_cluster
terraform state list | grep aws_vpc
terraform state list | grep aws_subnet

# Check state size (should be reasonable)
ls -lh terraform.tfstate

# Validate state
terraform state validate
```

#### 1.3.3 Documentation
- [ ] **Document outputs:**
  ```bash
  terraform output -json > phase1-outputs.json
  ```

- [ ] **Save kubeconfig:**
  ```bash
  aws eks update-kubeconfig --name cmbcluster-dev --region us-east-1
  # Saved to ~/.kube/config
  ```

- [ ] **Record cluster details:**
  ```
  Cluster Name: cmbcluster-dev
  Region: us-east-1
  Kubernetes Version: 1.28
  Node Count: 2
  Node Type: t3.medium
  VPC ID: vpc-xxxxx
  ```

**Checkpoint 1.3:** Phase 1 complete and validated

### 1.4 Rollback Test (Safety Check)

#### 1.4.1 Test Destroy
```bash
# OPTIONAL: Test that destroy works (don't actually run in production!)
# This validates that you can clean up if needed

# Plan destroy
terraform plan -destroy \
  -target=module.aws_eks \
  -target=module.aws_vpc \
  -var-file=dev.local.tfvars \
  -out=destroy.tfplan

# Show what would be destroyed
terraform show destroy.tfplan

# DO NOT APPLY - just verify it works
```

**Checkpoint 1.4:** Rollback procedure validated

---

## 💾 PHASE 2: Storage & IAM (S3 + Cognito)

**Duration:** Days 8-11
**Team:** 1 engineer (with DevOps review)
**Goal:** Add storage and identity services

### 2.1 S3 Storage Setup

#### 2.1.1 Plan S3 Buckets
```bash
# Create plan for S3
terraform plan \
  -target=module.aws_s3 \
  -var-file=dev.local.tfvars \
  -out=s3.tfplan

terraform show s3.tfplan
```

**Expected Resources:**
- 1 Database bucket (cmbcluster-dev-db-{account-id})
- User bucket prefix (cmbcluster-dev-user-*)
- Versioning enabled
- Encryption enabled
- Lifecycle policies

#### 2.1.2 Apply S3 Configuration
```bash
# Apply S3 buckets (takes ~2 minutes)
terraform apply s3.tfplan

# Get bucket names
terraform output aws_s3_bucket_names
terraform output aws_database_bucket

# Verify buckets exist
aws s3 ls | grep cmbcluster

# Check versioning
aws s3api get-bucket-versioning \
  --bucket $(terraform output -raw aws_database_bucket)

# Check encryption
aws s3api get-bucket-encryption \
  --bucket $(terraform output -raw aws_database_bucket)
```

**Checkpoint 2.1:** S3 buckets created

### 2.2 IAM Roles & IRSA Setup

#### 2.2.1 Plan IAM Resources
```bash
# Create plan for IAM
terraform plan \
  -target=module.aws_iam \
  -var-file=dev.local.tfvars \
  -out=iam.tfplan

terraform show iam.tfplan
```

**Expected Resources:**
- IRSA workload role
- S3 access policy
- ECR access policy
- ALB controller role
- Trust relationships configured

#### 2.2.2 Apply IAM Configuration
```bash
# Apply IAM roles (takes ~2 minutes)
terraform apply iam.tfplan

# Get role ARN
terraform output aws_iam_role_arn

# Verify role trust relationship
aws iam get-role --role-name cmbcluster-dev-workload-role \
  --query 'Role.AssumeRolePolicyDocument' | jq .
```

**Checkpoint 2.2:** IAM roles created

### 2.3 ECR Container Registries

#### 2.3.1 Plan ECR Repositories
```bash
# Create plan for ECR
terraform plan \
  -target=module.aws_ecr \
  -var-file=dev.local.tfvars \
  -out=ecr.tfplan

terraform show ecr.tfplan
```

**Expected Resources:**
- Backend repository
- Frontend repository
- Lifecycle policies (keep 10 latest)
- Image scanning enabled

#### 2.3.2 Apply ECR Configuration
```bash
# Apply ECR repositories (takes ~1 minute)
terraform apply ecr.tfplan

# Get registry URL
terraform output aws_ecr_registry_url

# Verify repositories
aws ecr describe-repositories --query 'repositories[*].repositoryName'

# Get login credentials
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $(terraform output -raw aws_ecr_registry_url)
```

**Checkpoint 2.3:** ECR repositories created

### 2.4 AWS Cognito Setup

#### 2.4.1 Plan Cognito Resources
```bash
# Create plan for Cognito
terraform plan \
  -target=module.aws_cognito \
  -var-file=dev.local.tfvars \
  -out=cognito.tfplan

terraform show cognito.tfplan
```

**Expected Resources:**
- User pool (cmbcluster-dev-users)
- App client (cmbcluster-dev-app)
- Cognito domain (cmbcluster-dev-auth)
- Password policies
- Email verification

#### 2.4.2 Apply Cognito Configuration
```bash
# Apply Cognito (takes ~3 minutes)
terraform apply cognito.tfplan

# Get Cognito details
terraform output aws_cognito_user_pool_id
terraform output aws_cognito_client_id
terraform output aws_cognito_issuer_url

# Store for later use
cat >> .env << 'EOF'
COGNITO_USER_POOL_ID=$(terraform output -raw aws_cognito_user_pool_id)
COGNITO_CLIENT_ID=$(terraform output -raw aws_cognito_client_id)
COGNITO_ISSUER=$(terraform output -raw aws_cognito_issuer_url)
EOF
```

**Checkpoint 2.4:** Cognito configured

### 2.5 Test IAM Permissions

#### 2.5.1 Verify S3 Access
```bash
# Test S3 access from pod (will do in Phase 3)
# For now, verify IAM policy

aws iam get-role-policy \
  --role-name cmbcluster-dev-workload-role \
  --policy-name s3-access

# Should show S3 permissions
```

#### 2.5.2 Verify ECR Access
```bash
# Test ECR access
aws ecr get-authorization-token --region us-east-1

# Try pushing a test image (optional)
docker tag busybox:latest $(terraform output -raw aws_ecr_registry_url)/test:latest
docker push $(terraform output -raw aws_ecr_registry_url)/test:latest
```

**Checkpoint 2.5:** IAM permissions verified

---

## 🎮 PHASE 3: Kubernetes & Application Deployment

**Duration:** Days 12-15
**Team:** 1 engineer (with DevOps review)
**Goal:** Deploy Kubernetes controllers and application

### 3.1 CSI Drivers Installation

#### 3.1.1 Plan CSI Drivers
```bash
# Create plan for CSI drivers
terraform plan \
  -target=module.csi_drivers \
  -var-file=dev.local.tfvars \
  -out=csi.tfplan

terraform show csi.tfplan
```

**Expected Resources:**
- S3 CSI Driver (Mountpoint for Amazon S3)
- EBS CSI Driver
- Service accounts
- DaemonSets for drivers

#### 3.1.2 Apply CSI Drivers
```bash
# Apply CSI drivers (takes ~5 minutes)
terraform apply csi.tfplan

# Verify CSI driver pods
kubectl get pods -n kube-system -l "app.kubernetes.io/name=aws-ebs-csi-driver"
kubectl get pods -n kube-system -l "app.kubernetes.io/name=aws-mountpoint-s3-csi-driver"

# Check CSI drivers available
kubectl get csidriver
```

**Checkpoint 3.1:** CSI drivers installed

### 3.2 cert-manager & TLS

#### 3.2.1 Plan cert-manager
```bash
# Create plan for cert-manager
terraform plan \
  -target=module.cert_manager \
  -var-file=dev.local.tfvars \
  -out=cert-manager.tfplan

terraform show cert-manager.tfplan
```

**Expected Resources:**
- cert-manager Helm chart
- ClusterIssuer (Let's Encrypt staging or prod)
- Namespace

#### 3.2.2 Apply cert-manager
```bash
# Apply cert-manager (takes ~3 minutes)
terraform apply cert-manager.tfplan

# Verify cert-manager
kubectl get pods -n cert-manager
kubectl get clusterissuer

# Expected: letsencrypt-staging or letsencrypt-prod
```

**Checkpoint 3.2:** cert-manager deployed

### 3.3 AWS Load Balancer Controller

#### 3.3.1 Plan ALB Controller
```bash
# Create plan for ALB controller
terraform plan \
  -target=module.aws_load_balancer_controller \
  -var-file=dev.local.tfvars \
  -out=alb-controller.tfplan

terraform show alb-controller.tfplan
```

**Expected Resources:**
- AWS Load Balancer Controller Helm chart
- Service account with IRSA role
- RBAC configuration

#### 3.3.2 Apply ALB Controller
```bash
# Apply ALB controller (takes ~3 minutes)
terraform apply alb-controller.tfplan

# Verify ALB controller
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# Check service account has IRSA annotation
kubectl get sa -n kube-system aws-load-balancer-controller -o yaml | grep role-arn
```

**Checkpoint 3.3:** ALB controller deployed

### 3.4 Application Deployment

#### 3.4.1 Plan Helm Deployment
```bash
# Create plan for application
terraform plan \
  -target=module.helm_deployment \
  -var-file=dev.local.tfvars \
  -out=helm.tfplan

terraform show helm.tfplan
```

**Expected Resources:**
- Kubernetes namespace (cmbcluster)
- Backend deployment
- Frontend deployment
- Services (LoadBalancer/ClusterIP)
- ConfigMaps & Secrets
- Ingress

#### 3.4.2 Apply Helm Deployment
```bash
# Apply Helm deployment (takes ~5 minutes)
terraform apply helm.tfplan

# Verify deployments
kubectl get deployments -n cmbcluster
kubectl get pods -n cmbcluster
kubectl get svc -n cmbcluster

# Check ingress
kubectl get ingress -n cmbcluster

# Wait for LoadBalancer IP
kubectl get svc -n cmbcluster -w
```

**Checkpoint 3.4.1:** Application deployed

#### 3.4.3 Get Load Balancer Address
```bash
# Get ALB DNS name
ALB_DNS=$(kubectl get svc -n cmbcluster cmbcluster-backend \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo "Load Balancer: $ALB_DNS"

# Check backend health
curl -i http://$ALB_DNS/health

# Expected: 200 OK
```

**Checkpoint 3.4.2:** Load balancer accessible

### 3.5 Verification & Testing

#### 3.5.1 Application Readiness
```bash
# Check pod logs
kubectl logs -n cmbcluster deployment/cmbcluster-backend

# Check environment variables
kubectl exec -it -n cmbcluster deployment/cmbcluster-backend -- env | grep CLOUD_PROVIDER

# Test API endpoint
curl http://$ALB_DNS/api/health
```

#### 3.5.2 Storage Access
```bash
# Verify S3 CSI driver is mounting buckets
# (Will test in pod lifecycle in Phase 4)

# Check persistent volume claims
kubectl get pvc -n cmbcluster
```

#### 3.5.3 TLS Certificate
```bash
# Check certificate status
kubectl get certificate -n cmbcluster

# Verify cert-manager issued certificate
kubectl describe certificate -n cmbcluster

# Expected: Ready = True
```

**Checkpoint 3.5:** Application verified

---

## 🌍 PHASE 4: GCP Parity & Validation

**Duration:** Days 16-19
**Team:** 1 engineer (with GCP specialist review)
**Goal:** Validate GCP deployment modules

### 4.1 GCP Network & GKE

#### 4.1.1 Plan GCP Infrastructure
```bash
# Create GCP-specific tfvars
cp terraform/environments/dev.tfvars terraform/gcp.local.tfvars

# Edit for GCP
cat >> terraform/gcp.local.tfvars << 'EOF'
cloud_provider  = "gcp"
gcp_project_id  = "your-gcp-project-id"
gcp_region      = "us-central1"
EOF

# Plan GCP resources
terraform plan \
  -var-file=gcp.local.tfvars \
  -out=gcp.tfplan

terraform show gcp.tfplan
```

**Expected Resources:**
- GCP VPC network
- Subnets (3 regions)
- GKE cluster
- Node pool
- Cloud NAT

#### 4.1.2 Apply GCP Infrastructure
```bash
# Apply GCP infrastructure (takes ~20-25 minutes)
terraform apply gcp.tfplan

# Get kubeconfig for GCP
eval "$(terraform output -raw kubeconfig_command)"

# Verify GKE cluster
kubectl cluster-info
kubectl get nodes
```

**Checkpoint 4.1:** GCP infrastructure deployed

### 4.2 GCP Storage & IAM

#### 4.2.1 Plan GCS Buckets
```bash
# Plan GCS storage
terraform plan \
  -target=module.gcp_storage \
  -var-file=gcp.local.tfvars \
  -out=gcs.tfplan

terraform apply gcs.tfplan

# Verify buckets
gsutil ls -p your-gcp-project-id
```

#### 4.2.2 Plan Workload Identity
```bash
# Plan Workload Identity configuration
terraform plan \
  -target=module.gcp_iam \
  -var-file=gcp.local.tfvars \
  -out=gcp-iam.tfplan

terraform apply gcp-iam.tfplan

# Verify service accounts
gcloud iam service-accounts list
```

**Checkpoint 4.2:** GCP storage & IAM configured

### 4.3 GCP Application Deployment

#### 4.3.1 Deploy CSI Drivers & Application
```bash
# Plan Kubernetes resources (reuse from Phase 3)
terraform plan \
  -target=module.kubernetes_namespaces \
  -target=module.csi_drivers \
  -target=module.cert_manager \
  -var-file=gcp.local.tfvars \
  -out=gcp-k8s.tfplan

terraform apply gcp-k8s.tfplan

# Deploy application
terraform apply \
  -var-file=gcp.local.tfvars
```

**Checkpoint 4.3:** Application deployed on GCP

### 4.4 Comparison Testing

#### 4.4.1 AWS vs GCP Comparison
```bash
# Test AWS cluster
kubectl config use-context arn:aws:eks:us-east-1:ACCOUNT:cluster/cmbcluster-dev

# Get endpoints
aws_api=$(kubectl config view -o jsonpath='{.clusters[0].cluster.server}')

# Switch to GCP
kubectl config use-context gke_PROJECT_REGION_CLUSTER

gcp_api=$(kubectl config view -o jsonpath='{.clusters[0].cluster.server}')

# Compare configurations
echo "AWS API: $aws_api"
echo "GCP API: $gcp_api"

# Test both clusters work identically
kubectl get nodes -o wide  # AWS
kubectl get nodes -o wide  # GCP
```

**Checkpoint 4.4:** Both clouds validated

---

## ✅ PHASE 5: Cutover & Shell Script Deprecation

**Duration:** Days 20-21
**Team:** 1 engineer + DevOps lead
**Goal:** Complete migration from shell scripts to Terraform

### 5.1 Parallel Verification

#### 5.1.1 Run Both Systems
```bash
# Keep shell script infrastructure running
# Keep Terraform infrastructure running
# Both should coexist for 1-2 days

# Verify both are healthy
./scripts/aws/deploy.sh --dry-run  # Shell scripts
terraform plan                      # Terraform

# Load test both
ab -n 1000 -c 10 https://api.shell-script-cluster.local
ab -n 1000 -c 10 https://api.terraform-cluster.local

# Both should perform similarly
```

**Checkpoint 5.1:** Both systems running and verified

### 5.2 Cutover to Terraform

#### 5.2.1 Update Documentation
- [ ] Mark shell scripts as deprecated
  ```bash
  # Add header to all shell scripts
  cat > scripts/DEPRECATED.md << 'EOF'
  # DEPRECATED SCRIPTS

  These shell scripts are deprecated as of 2025-10-24.
  Please use Terraform for infrastructure management:

  See: TERRAFORM_IMPLEMENTATION_GUIDE.md
  EOF
  ```

- [ ] Update README
  ```markdown
  ## Infrastructure Management

  **CURRENT METHOD:** Terraform
  **See:** TERRAFORM_IMPLEMENTATION_GUIDE.md

  Legacy shell scripts are deprecated.
  ```

#### 5.2.2 Migrate to Remote State
```bash
# Uncomment backend in main.tf
cat >> terraform/backend.tf << 'EOF'
terraform {
  backend "s3" {
    bucket         = "cmbcluster-terraform-state-aws"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
EOF

# Migrate local state to S3
terraform init

# Verify migration
terraform state pull > state-backup.json
aws s3 ls s3://cmbcluster-terraform-state-aws/dev/
```

**Checkpoint 5.2:** Migrated to remote state

#### 5.2.3 Update CI/CD

Create GitHub Actions workflow:
```yaml
# .github/workflows/terraform.yml
name: Terraform CI/CD

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

      - name: Terraform Init
        run: terraform init

      - name: Terraform Plan
        run: terraform plan -out=tfplan

      - name: Terraform Apply (main only)
        if: github.ref == 'refs/heads/main'
        run: terraform apply tfplan
```

**Checkpoint 5.2.3:** CI/CD configured

### 5.3 Team Training & Handoff

#### 5.3.1 Team Workshop
- [ ] **Present Terraform workflow**
  - [ ] Code structure
  - [ ] Variable management
  - [ ] State management
  - [ ] Plan & apply process

- [ ] **Hands-on practice**
  - [ ] Each engineer runs terraform plan
  - [ ] Each engineer reviews and applies
  - [ ] Practice rollback procedures
  - [ ] Practice troubleshooting

#### 5.3.2 Documentation Handoff
- [ ] Terraform implementation guide
- [ ] Module documentation
- [ ] Troubleshooting guide
- [ ] Emergency procedures
- [ ] Runbooks

**Checkpoint 5.3:** Team trained and confident

### 5.4 Final Validation

#### 5.4.1 Acceptance Criteria
```bash
# Verify all acceptance criteria met
✅ Infrastructure deploys via Terraform
✅ State managed in S3/GCS
✅ Both AWS and GCP working
✅ CI/CD pipeline functional
✅ Team trained on procedures
✅ Documentation complete
✅ Rollback tested and working
✅ Monitoring/alerting functional
```

#### 5.4.2 Decommission Shell Scripts
```bash
# Archive shell scripts (don't delete yet)
mkdir -p archive/shell-scripts
mv scripts/aws/*.sh archive/shell-scripts/
mv scripts/gcp/*.sh archive/shell-scripts/

# Add deprecation notice
echo "Legacy shell scripts - see TERRAFORM_IMPLEMENTATION_GUIDE.md" > scripts/DEPRECATED.md

# Commit changes
git add scripts/ terraform/ docs/
git commit -m "feat: Migrate to Terraform, deprecate shell scripts

- Remove shell scripts from active use
- Terraform manages all infrastructure
- Remote state in S3
- CI/CD pipeline integrated
- Team trained on new workflow"

git push origin feature/terraform-implementation
```

**Checkpoint 5.4:** Cutover complete

### 5.5 Post-Cutover Tasks (Week 2)

#### 5.5.1 Monitoring & Alerting
- [ ] Set up CloudWatch/Cloud Monitoring for infrastructure
- [ ] Alert on failed Terraform runs
- [ ] Alert on state file modifications
- [ ] Monitor resource costs

#### 5.5.2 Optimization
- [ ] Review execution times
- [ ] Optimize parallelism
- [ ] Add auto-scaling policies
- [ ] Implement cost optimization

#### 5.5.3 Documentation Updates
- [ ] Update runbooks
- [ ] Document common issues
- [ ] Create troubleshooting guide
- [ ] Update architectural diagrams

---

## 📊 Timeline Overview

```
Week 1: Preparation & Core Infrastructure
├─ Days 1-3:  Phase 0 - Prep (tools, credentials, training)
├─ Days 4-7:  Phase 1 - VPC + EKS
├─ Days 8-11: Phase 2 - S3 + IAM + Cognito

Week 2: Application & Validation
├─ Days 12-15: Phase 3 - Kubernetes + Application
├─ Days 16-19: Phase 4 - GCP validation
├─ Days 20-21: Phase 5 - Cutover
└─ Days 22-28: Stabilization + optimization

**Total: 4 weeks**
```

---

## ✅ Success Criteria Checklist

### Completion Criteria
- [ ] All Terraform modules deployed successfully
- [ ] Both AWS and GCP infrastructure functional
- [ ] State management configured (remote backend)
- [ ] CI/CD pipeline integrated
- [ ] Team trained on Terraform workflow
- [ ] Documentation complete and reviewed
- [ ] Shell scripts deprecated (archived)
- [ ] Monitoring configured
- [ ] Zero-downtime cutover completed
- [ ] No production incidents

### Quality Metrics
- [ ] Terraform code passes validation & linting
- [ ] No hard-coded values or credentials
- [ ] Comprehensive error handling
- [ ] All resources tagged properly
- [ ] State file backed up and versioned
- [ ] Destroy/rollback tested successfully
- [ ] Documentation reviewed by DevOps lead

### Acceptance Sign-offs
- [ ] Engineer: "Code is ready for production"
- [ ] DevOps Lead: "Infrastructure is production-ready"
- [ ] Engineering Manager: "Team is confident with process"
- [ ] CTO: "Approved for production deployment"

---

## 🚨 Rollback Plan

If issues occur during any phase:

### Immediate Rollback (Any Phase)
```bash
# Destroy only the problematic resources
terraform destroy -target=<resource> -var-file=dev.local.tfvars

# Or destroy entire phase
terraform destroy -target=<module_name> -var-file=dev.local.tfvars

# Keep shell scripts running as fallback
# User traffic continues on old infrastructure
```

### Full Rollback (If Needed)
```bash
# Keep Terraform state for reference
terraform state pull > backup.json

# Destroy all Terraform resources
terraform destroy -var-file=dev.local.tfvars

# Switch all traffic to shell script infrastructure
# Investigate issues, fix code, and retry

# Or keep both systems running until confident
```

---

## 📝 Daily Standup Template

```markdown
## Terraform Migration Daily Standup

**Date:** [Date]
**Phase:** [0-5]
**Status:** [In Progress]

### What was completed yesterday?
- [ ] Item 1
- [ ] Item 2

### What will be completed today?
- [ ] Item 1
- [ ] Item 2

### Blockers or Issues
- [ ] Blocker 1: [Description] - [Mitigation]

### Metrics
- Resources created: X
- Terraform state size: Y MB
- Deployment time: Z minutes

### Notes
-
```

---

## 🎓 Reference Materials

### During Implementation
- TERRAFORM_IMPLEMENTATION_GUIDE.md ← Main reference
- Module code ← Implementation details
- Terraform Registry ← Provider documentation

### Training Materials
- TERRAFORM_VS_SHELL_SCRIPTS.md
- Architecture diagrams
- Video walkthroughs (optional)

---

## 📞 Support & Escalation

**Questions?** → Review TERRAFORM_IMPLEMENTATION_GUIDE.md
**Blockers?** → Escalate to DevOps lead
**Production issue?** → Activate rollback plan

---

## Conclusion

This phased approach ensures:

✅ **Zero downtime** - Parallel infrastructure
✅ **Validated** - Testing at each phase
✅ **Trained** - Team prepared for handoff
✅ **Documented** - Comprehensive reference materials
✅ **Safe** - Rollback capability throughout
✅ **Production-ready** - Following best practices

**Ready to proceed? Start with Phase 0!** 🚀

---

**Prepared by:** Comprehensive Terraform Planning
**Status:** ✅ **READY FOR IMPLEMENTATION**
**Approval:** Pending Phase 0 kickoff

