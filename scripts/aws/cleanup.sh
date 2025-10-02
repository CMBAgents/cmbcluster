#!/bin/bash
set -e

# CMBCluster AWS EKS Cleanup Script
# This script tears down all AWS resources created for CMBCluster.
# Use with caution - this will delete your cluster and all data!
#
# Usage:
#   ./scripts/aws/cleanup.sh [CLUSTER_NAME] [AWS_REGION]

# --- Configuration Loading ---
if [ -f .env ]; then
  echo "Loading environment variables from .env file..."
  set -o allexport
  source .env
  set +o allexport
fi

# --- Variable Definitions ---
CLUSTER_NAME=${1:-$CLUSTER_NAME}
AWS_REGION=${2:-$AWS_REGION}

# Set defaults
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text 2>/dev/null)}
CLUSTER_NAME=${CLUSTER_NAME:-"cmbcluster"}
AWS_REGION=${AWS_REGION:-"us-east-1"}

# Validate
if [ -z "$AWS_ACCOUNT_ID" ]; then
  echo "Error: Could not determine AWS Account ID."
  exit 1
fi

echo "WARNING: This will delete all CMBCluster resources in AWS!"
echo "AWS Account:  $AWS_ACCOUNT_ID"
echo "Cluster:      $CLUSTER_NAME"
echo "Region:       $AWS_REGION"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
  echo "Cleanup cancelled."
  exit 0
fi

# Resource naming
ECR_REPO_NAME="${CLUSTER_NAME}-images"
S3_BUCKET_DB="${AWS_ACCOUNT_ID}-${CLUSTER_NAME}-db"
S3_BUCKET_USER_PREFIX="${AWS_ACCOUNT_ID}-${CLUSTER_NAME}-user"
IAM_ROLE_NAME="${CLUSTER_NAME}-workload-role"
WORKLOAD_POLICY_NAME="${CLUSTER_NAME}-workload-policy"
ALB_POLICY_NAME="${CLUSTER_NAME}-AWSLoadBalancerControllerIAMPolicy"

echo "Starting cleanup process..."

# Delete Helm release
echo ""
echo "Deleting Helm release..."
helm uninstall cmbcluster --namespace cmbcluster 2>/dev/null || echo "Helm release not found or already deleted"

# Delete namespace (this will delete all resources in it)
echo ""
echo "Deleting namespace..."
kubectl delete namespace cmbcluster --ignore-not-found=true --timeout=5m

# Delete EKS cluster
echo ""
echo "Deleting EKS cluster (this may take 10-15 minutes)..."
if aws eks describe-cluster --name $CLUSTER_NAME --region $AWS_REGION >/dev/null 2>&1; then
  eksctl delete cluster --name $CLUSTER_NAME --region $AWS_REGION --wait
  echo "EKS cluster deleted"
else
  echo "EKS cluster not found or already deleted"
fi

# Delete ECR repository
echo ""
echo "Deleting ECR repository..."
if aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION >/dev/null 2>&1; then
  aws ecr delete-repository \
    --repository-name $ECR_REPO_NAME \
    --region $AWS_REGION \
    --force
  echo "ECR repository deleted"
else
  echo "ECR repository not found or already deleted"
fi

# Delete S3 buckets
echo ""
echo "Deleting S3 buckets..."

# Delete database bucket
if aws s3 ls "s3://${S3_BUCKET_DB}" 2>/dev/null; then
  echo "Emptying and deleting database bucket: $S3_BUCKET_DB"
  aws s3 rm "s3://${S3_BUCKET_DB}" --recursive
  aws s3api delete-bucket --bucket $S3_BUCKET_DB --region $AWS_REGION
  echo "Database bucket deleted"
else
  echo "Database bucket not found or already deleted"
fi

# Delete user buckets
echo "Searching for user buckets with prefix: ${S3_BUCKET_USER_PREFIX}-*"
USER_BUCKETS=$(aws s3api list-buckets --query "Buckets[?starts_with(Name, '${S3_BUCKET_USER_PREFIX}-')].Name" --output text)

if [ -n "$USER_BUCKETS" ]; then
  for bucket in $USER_BUCKETS; do
    echo "Emptying and deleting user bucket: $bucket"
    aws s3 rm "s3://${bucket}" --recursive
    aws s3api delete-bucket --bucket $bucket --region $AWS_REGION
  done
  echo "User buckets deleted"
else
  echo "No user buckets found"
fi

# Detach and delete IAM policies
echo ""
echo "Cleaning up IAM policies and roles..."

# Detach and delete workload policy
WORKLOAD_POLICY_ARN=$(aws iam list-policies --scope Local --query "Policies[?PolicyName=='${WORKLOAD_POLICY_NAME}'].Arn" --output text)
if [ -n "$WORKLOAD_POLICY_ARN" ]; then
  echo "Detaching workload policy from role..."
  aws iam detach-role-policy --role-name $IAM_ROLE_NAME --policy-arn $WORKLOAD_POLICY_ARN 2>/dev/null || true
  echo "Deleting workload policy..."
  aws iam delete-policy --policy-arn $WORKLOAD_POLICY_ARN 2>/dev/null || true
  echo "Workload policy deleted"
fi

# Delete IAM role
if aws iam get-role --role-name $IAM_ROLE_NAME >/dev/null 2>&1; then
  echo "Deleting IAM role: $IAM_ROLE_NAME"
  aws iam delete-role --role-name $IAM_ROLE_NAME
  echo "IAM role deleted"
fi

# Delete ALB controller policy
ALB_POLICY_ARN=$(aws iam list-policies --scope Local --query "Policies[?PolicyName=='${ALB_POLICY_NAME}'].Arn" --output text)
if [ -n "$ALB_POLICY_ARN" ]; then
  echo "Deleting ALB controller policy..."
  aws iam delete-policy --policy-arn $ALB_POLICY_ARN 2>/dev/null || true
  echo "ALB controller policy deleted"
fi

echo ""
echo "Cleanup complete!"
echo ""
echo "All CMBCluster resources have been removed from AWS."
echo ""
echo "Note: The following may still exist and require manual cleanup:"
echo "- VPC and networking resources (if created outside eksctl)"
echo "- CloudWatch log groups"
echo "- Any manually created resources"
echo ""
echo "To verify all resources are deleted:"
echo "  aws eks list-clusters --region $AWS_REGION"
echo "  aws ecr describe-repositories --region $AWS_REGION"
echo "  aws s3 ls | grep $CLUSTER_NAME"
echo "  aws iam list-roles | grep $CLUSTER_NAME"
