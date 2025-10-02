#!/bin/bash
set -e

# CMBCluster AWS EKS Infrastructure Setup Script
# This script creates the AWS infrastructure needed to run CMBCluster on EKS.
# It mirrors the functionality of the GCP setup-cluster.sh script.
#
# Prerequisites:
# - AWS CLI configured with appropriate credentials
# - kubectl installed
# - eksctl installed
# - helm installed
#
# Usage:
#   ./scripts/aws/setup-cluster.sh [CLUSTER_NAME] [AWS_REGION] [AWS_ACCOUNT_ID]

# --- Configuration Loading ---
# 1. Load defaults from .env file if it exists
# 2. Allow overrides from command-line arguments
# 3. Set final defaults for any remaining unset variables

if [ -f .env ]; then
  echo " Loading environment variables from .env file..."
  set -o allexport
  source .env
  set +o allexport
fi

# --- Variable Definitions & Precedence ---
# Command-line arguments override .env file values
CLUSTER_NAME=${1:-$CLUSTER_NAME}
AWS_REGION=${2:-$AWS_REGION}
AWS_ACCOUNT_ID=${3:-$AWS_ACCOUNT_ID}

# Set final defaults if variables are still not set
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text 2>/dev/null)}
CLUSTER_NAME=${CLUSTER_NAME:-"cmbcluster"}
AWS_REGION=${AWS_REGION:-"us-east-1"}

# Validate required variables
if [ -z "$AWS_ACCOUNT_ID" ]; then
  echo " Error: Could not determine AWS Account ID."
  echo "Please ensure AWS CLI is configured or pass AWS_ACCOUNT_ID as argument."
  echo "Usage: $0 [CLUSTER_NAME] [AWS_REGION] [AWS_ACCOUNT_ID]"
  exit 1
fi

if [ -z "$CLUSTER_NAME" ]; then
  echo " Error: CLUSTER_NAME is required."
  echo "Usage: $0 [CLUSTER_NAME] [AWS_REGION] [AWS_ACCOUNT_ID]"
  exit 1
fi

echo " Setting up CMBCluster EKS infrastructure on AWS..."
echo "AWS Account:  $AWS_ACCOUNT_ID"
echo "Cluster:      $CLUSTER_NAME"
echo "Region:       $AWS_REGION"

# Set up resource naming
VPC_NAME="${CLUSTER_NAME}-vpc"
ECR_REPO_NAME="${CLUSTER_NAME}-images"
S3_BUCKET_DB="${AWS_ACCOUNT_ID}-${CLUSTER_NAME}-db"
S3_BUCKET_USER_PREFIX="${AWS_ACCOUNT_ID}-${CLUSTER_NAME}-user"
IAM_ROLE_NAME="${CLUSTER_NAME}-workload-role"
OIDC_PROVIDER_NAME="${CLUSTER_NAME}-oidc-provider"

# --- Create ECR Repository ---
echo ""
echo " Creating ECR repository for container images..."
if aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION >/dev/null 2>&1; then
  echo " ECR repository '$ECR_REPO_NAME' already exists"
else
  aws ecr create-repository \
    --repository-name $ECR_REPO_NAME \
    --region $AWS_REGION \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256 \
    --tags Key=Project,Value=CMBCluster Key=ManagedBy,Value=Script
  echo " ECR repository '$ECR_REPO_NAME' created"
fi

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
echo "   ECR URI: $ECR_URI"

# --- Create S3 Bucket for Database Storage ---
echo ""
echo " Creating S3 bucket for database storage..."
if aws s3 ls "s3://${S3_BUCKET_DB}" 2>/dev/null; then
  echo " S3 bucket '$S3_BUCKET_DB' already exists"
else
  # Create bucket with region-specific command
  if [ "$AWS_REGION" = "us-east-1" ]; then
    aws s3api create-bucket \
      --bucket $S3_BUCKET_DB \
      --region $AWS_REGION
  else
    aws s3api create-bucket \
      --bucket $S3_BUCKET_DB \
      --region $AWS_REGION \
      --create-bucket-configuration LocationConstraint=$AWS_REGION
  fi

  # Enable versioning for backup/recovery
  aws s3api put-bucket-versioning \
    --bucket $S3_BUCKET_DB \
    --versioning-configuration Status=Enabled

  # Enable encryption
  aws s3api put-bucket-encryption \
    --bucket $S3_BUCKET_DB \
    --server-side-encryption-configuration '{
            "Rules": [{
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }]
        }'

  # Set lifecycle policy to manage versions (keep last 30 versions)
  aws s3api put-bucket-lifecycle-configuration \
    --bucket $S3_BUCKET_DB \
    --lifecycle-configuration '{
            "Rules": [{
                "Id": "DeleteOldVersions",
                "Status": "Enabled",
                "NoncurrentVersionExpiration": {
                    "NoncurrentDays": 30
                }
            }]
        }'

  # Add tags
  aws s3api put-bucket-tagging \
    --bucket $S3_BUCKET_DB \
    --tagging 'TagSet=[{Key=Project,Value=CMBCluster},{Key=ManagedBy,Value=Script}]'

  echo " S3 bucket '$S3_BUCKET_DB' created with versioning and encryption enabled"
fi

# --- Step 3: Create EKS Cluster with VPC ---
echo ""
echo "  Creating EKS cluster with VPC and networking..."

# Check if cluster already exists
if aws eks describe-cluster --name $CLUSTER_NAME --region $AWS_REGION >/dev/null 2>&1; then
  echo " EKS cluster '$CLUSTER_NAME' already exists"
else
  # Create cluster configuration file
  cat >/tmp/${CLUSTER_NAME}-cluster-config.yaml <<EOF
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: ${CLUSTER_NAME}
  region: ${AWS_REGION}
  version: "1.28"

# VPC Configuration
vpc:
  cidr: 10.0.0.0/16
  nat:
    gateway: Single  # Use single NAT gateway for cost optimization
  clusterEndpoints:
    publicAccess: true
    privateAccess: true

# IAM OIDC Provider (required for IRSA - IAM Roles for Service Accounts)
iam:
  withOIDC: true

# Managed Node Group
managedNodeGroups:
  - name: ${CLUSTER_NAME}-ng-1
    instanceType: t3.medium
    minSize: 1
    maxSize: 3
    desiredCapacity: 1
    volumeSize: 50
    volumeType: gp3
    privateNetworking: true
    iam:
      withAddonPolicies:
        imageBuilder: true
        autoScaler: true
        ebs: true
        efs: true
        awsLoadBalancerController: true
        cloudWatch: true
    labels:
      role: worker
      environment: production
    tags:
      Project: CMBCluster
      ManagedBy: eksctl
    ssh:
      allow: false

# CloudWatch Logging
cloudWatch:
  clusterLogging:
    enableTypes: ["api", "audit", "authenticator", "controllerManager", "scheduler"]
    logRetentionInDays: 7

# Addons
addons:
  - name: vpc-cni
    version: latest
  - name: coredns
    version: latest
  - name: kube-proxy
    version: latest
  - name: aws-ebs-csi-driver
    version: latest
    attachPolicyARNs:
      - arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy
EOF

  echo "Creating EKS cluster (this will take 15-20 minutes)..."
  eksctl create cluster -f /tmp/${CLUSTER_NAME}-cluster-config.yaml

  echo " EKS cluster '$CLUSTER_NAME' created successfully"
  rm /tmp/${CLUSTER_NAME}-cluster-config.yaml
fi

# Update kubeconfig
echo ""
echo " Updating kubeconfig..."
aws eks update-kubeconfig --name $CLUSTER_NAME --region $AWS_REGION

# Verify cluster access
echo ""
echo " Verifying cluster access..."
kubectl get nodes

# --- Step 4: Install AWS Load Balancer Controller ---
echo ""
echo " Installing AWS Load Balancer Controller..."

# Check if already installed
if kubectl get deployment -n kube-system aws-load-balancer-controller >/dev/null 2>&1; then
  echo " AWS Load Balancer Controller already installed"
else
  # Create IAM policy for ALB controller
  echo "Creating IAM policy for ALB controller..."
  curl -o /tmp/iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.6.2/docs/install/iam_policy.json

  ALB_POLICY_NAME="${CLUSTER_NAME}-AWSLoadBalancerControllerIAMPolicy"
  ALB_POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='${ALB_POLICY_NAME}'].Arn" --output text)

  if [ -z "$ALB_POLICY_ARN" ]; then
    ALB_POLICY_ARN=$(aws iam create-policy \
      --policy-name $ALB_POLICY_NAME \
      --policy-document file:///tmp/iam_policy.json \
      --query 'Policy.Arn' --output text)
    echo "Created IAM policy: $ALB_POLICY_ARN"
  else
    echo "IAM policy already exists: $ALB_POLICY_ARN"
  fi
  rm /tmp/iam_policy.json

  # Create service account with IAM role
  eksctl create iamserviceaccount \
    --cluster=$CLUSTER_NAME \
    --namespace=kube-system \
    --name=aws-load-balancer-controller \
    --attach-policy-arn=$ALB_POLICY_ARN \
    --override-existing-serviceaccounts \
    --region=$AWS_REGION \
    --approve

  # Install AWS Load Balancer Controller using Helm
  helm repo add eks https://aws.github.io/eks-charts
  helm repo update

  helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
    -n kube-system \
    --set clusterName=$CLUSTER_NAME \
    --set serviceAccount.create=false \
    --set serviceAccount.name=aws-load-balancer-controller \
    --set region=$AWS_REGION \
    --set vpcId=$(aws eks describe-cluster --name $CLUSTER_NAME --region $AWS_REGION --query "cluster.resourcesVpcConfig.vpcId" --output text)

  echo " Waiting for AWS Load Balancer Controller to be ready..."
  kubectl wait --namespace kube-system \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/name=aws-load-balancer-controller \
    --timeout=300s

  echo " AWS Load Balancer Controller installed successfully"
fi

# --- Step 5: Install cert-manager ---
echo ""
echo " Installing cert-manager for SSL certificates..."

if kubectl get namespace cert-manager >/dev/null 2>&1; then
  echo " cert-manager already installed"
else
  kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml

  echo " Waiting for cert-manager to be ready..."
  kubectl wait --namespace cert-manager \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/instance=cert-manager \
    --timeout=300s

  # Create ClusterIssuer for Let's Encrypt
  if [ -z "$LETSENCRYPT_EMAIL" ] || [ "$LETSENCRYPT_EMAIL" = "your-email@example.com" ]; then
    echo "  Warning: LETSENCRYPT_EMAIL is not set or is the default value."
    echo "Please set a valid email in your .env file for Let's Encrypt notifications."
    echo "Skipping ClusterIssuer creation - you'll need to create it manually."
  else
    cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ${LETSENCRYPT_EMAIL}
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: alb
EOF
    echo " Let's Encrypt ClusterIssuer created"
  fi

  echo " cert-manager installed successfully"
fi

# --- Step 6: Create IAM Role for Workload Identity (IRSA) ---
echo ""
echo " Setting up IAM Role for Service Accounts (IRSA)..."

# Get OIDC provider URL
OIDC_PROVIDER=$(aws eks describe-cluster --name $CLUSTER_NAME --region $AWS_REGION --query "cluster.identity.oidc.issuer" --output text | sed -e "s/^https:\/\///")
echo "OIDC Provider: $OIDC_PROVIDER"

# Check if IAM role exists
if aws iam get-role --role-name $IAM_ROLE_NAME >/dev/null 2>&1; then
  echo " IAM role '$IAM_ROLE_NAME' already exists"
else
  # Create trust policy for IRSA
  cat >/tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/${OIDC_PROVIDER}"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "${OIDC_PROVIDER}:sub": "system:serviceaccount:cmbcluster:cmbcluster-ksa",
          "${OIDC_PROVIDER}:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
EOF

  # Create IAM role
  aws iam create-role \
    --role-name $IAM_ROLE_NAME \
    --assume-role-policy-document file:///tmp/trust-policy.json \
    --description "IAM role for CMBCluster workload identity" \
    --tags Key=Project,Value=CMBCluster Key=ManagedBy,Value=Script

  rm /tmp/trust-policy.json
  echo " IAM role '$IAM_ROLE_NAME' created"
fi

# Create and attach IAM policy for S3 and ECR access
echo "Creating IAM policy for S3 and ECR access..."
cat >/tmp/workload-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::${S3_BUCKET_DB}",
        "arn:aws:s3:::${S3_BUCKET_DB}/*",
        "arn:aws:s3:::${S3_BUCKET_USER_PREFIX}-*",
        "arn:aws:s3:::${S3_BUCKET_USER_PREFIX}-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:PutBucketVersioning",
        "s3:PutBucketEncryption",
        "s3:PutBucketTagging"
      ],
      "Resource": "arn:aws:s3:::${S3_BUCKET_USER_PREFIX}-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    }
  ]
}
EOF

WORKLOAD_POLICY_NAME="${CLUSTER_NAME}-workload-policy"
WORKLOAD_POLICY_ARN=$(aws iam list-policies --scope Local --query "Policies[?PolicyName=='${WORKLOAD_POLICY_NAME}'].Arn" --output text)

if [ -z "$WORKLOAD_POLICY_ARN" ]; then
  WORKLOAD_POLICY_ARN=$(aws iam create-policy \
    --policy-name $WORKLOAD_POLICY_NAME \
    --policy-document file:///tmp/workload-policy.json \
    --query 'Policy.Arn' --output text)
  echo "Created workload policy: $WORKLOAD_POLICY_ARN"
else
  echo "Workload policy already exists: $WORKLOAD_POLICY_ARN"
fi

rm /tmp/workload-policy.json

# Attach policy to role
aws iam attach-role-policy \
  --role-name $IAM_ROLE_NAME \
  --policy-arn $WORKLOAD_POLICY_ARN

echo " IAM policies attached to role '$IAM_ROLE_NAME'"

# --- Step 7: Create Storage Class ---
echo ""
echo " Creating storage class for persistent volumes..."

kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: cmbcluster-ssd
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
allowVolumeExpansion: true
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
EOF

echo " Storage class 'cmbcluster-ssd' created"

# --- Summary ---
echo ""
echo " CMBCluster EKS infrastructure setup complete!"
echo ""
echo " Summary:"
echo "- AWS Account: $AWS_ACCOUNT_ID"
echo "- Region: $AWS_REGION"
echo "- Cluster: $CLUSTER_NAME"
echo "- ECR Repository: $ECR_URI"
echo "- S3 Database Bucket: s3://${S3_BUCKET_DB}"
echo "- S3 User Bucket Prefix: s3://${S3_BUCKET_USER_PREFIX}-*"
echo "- IAM Role: $IAM_ROLE_NAME"
echo "- IAM Role ARN: arn:aws:iam::${AWS_ACCOUNT_ID}:role/${IAM_ROLE_NAME}"
echo ""
echo " Next steps:"
echo "1. Configure your domain DNS to point to the ALB"
echo "2. Set up OAuth credentials (Google or other provider)"
echo "3. Update helm/values.yaml with AWS-specific values"
echo "4. Run: ./scripts/aws/deploy.sh $CLUSTER_NAME $AWS_REGION your-domain.com"
echo ""
echo " Useful commands:"
echo "kubectl get nodes"
echo "kubectl get pods -A"
echo "aws eks describe-cluster --name $CLUSTER_NAME --region $AWS_REGION"
