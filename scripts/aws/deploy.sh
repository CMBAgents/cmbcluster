#!/bin/bash
set -e

# CMBCluster AWS EKS Deployment Script
# This script deploys the CMBCluster application to AWS EKS using Helm.
# It mirrors the functionality of the GCP deploy.sh script.
#
# Prerequisites:
# - EKS cluster already created (run setup-cluster.sh first)
# - kubectl configured with cluster access
# - helm installed
# - Docker images built and pushed to ECR
#
# Usage:
#   ./scripts/aws/deploy.sh [CLUSTER_NAME] [AWS_REGION] [BASE_DOMAIN]

# --- Configuration Loading ---
if [ -f .env ]; then
  echo "Loading environment variables from .env file..."
  set -o allexport
  source .env
  set +o allexport
fi

# --- Variable Definitions & Precedence ---
CLUSTER_NAME=${1:-$CLUSTER_NAME}
AWS_REGION=${2:-$AWS_REGION}
BASE_DOMAIN=${3:-$BASE_DOMAIN}

# Set final defaults
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text 2>/dev/null)}
CLUSTER_NAME=${CLUSTER_NAME:-"cmbcluster"}
AWS_REGION=${AWS_REGION:-"us-east-1"}
NAMESPACE=${NAMESPACE:-"cmbcluster"}

# Validate required variables
if [ -z "$AWS_ACCOUNT_ID" ]; then
  echo "Error: Could not determine AWS Account ID."
  exit 1
fi

if [ -z "$BASE_DOMAIN" ]; then
  echo "Error: BASE_DOMAIN is required."
  echo "Usage: $0 [CLUSTER_NAME] [AWS_REGION] [BASE_DOMAIN]"
  exit 1
fi

if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ] || [ -z "$SECRET_KEY" ]; then
  echo "Error: Missing required environment variables."
  echo "Please set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and SECRET_KEY in .env file."
  exit 1
fi

echo "Deploying CMBCluster to AWS EKS..."
echo "AWS Account:  $AWS_ACCOUNT_ID"
echo "Cluster:      $CLUSTER_NAME"
echo "Region:       $AWS_REGION"
echo "Namespace:    $NAMESPACE"
echo "Domain:       $BASE_DOMAIN"

# Set up resource naming
ECR_REPO_NAME="${CLUSTER_NAME}-images"
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
IAM_ROLE_NAME="${CLUSTER_NAME}-workload-role"
IAM_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${IAM_ROLE_NAME}"

# Update kubeconfig
echo ""
echo "Updating kubeconfig..."
aws eks update-kubeconfig --name $CLUSTER_NAME --region $AWS_REGION

# Create namespace if it doesn't exist
echo ""
echo "Creating namespace '$NAMESPACE'..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create Kubernetes service account with IAM role annotation (IRSA)
echo ""
echo "Creating Kubernetes service account with IAM role annotation..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cmbcluster-ksa
  namespace: $NAMESPACE
  annotations:
    eks.amazonaws.com/role-arn: $IAM_ROLE_ARN
EOF

# Create low-privilege service account for user pods
echo ""
echo "Creating low-privilege service account for user pods..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cmbcluster-user-sa
  namespace: $NAMESPACE
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: cmbcluster-user-role
  namespace: $NAMESPACE
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: cmbcluster-user-rolebinding
  namespace: $NAMESPACE
subjects:
- kind: ServiceAccount
  name: cmbcluster-user-sa
  namespace: $NAMESPACE
roleRef:
  kind: Role
  name: cmbcluster-user-role
  apiGroup: rbac.authorization.k8s.io
EOF

# Create Kubernetes secret for backend
echo ""
echo "Creating Kubernetes secret for sensitive environment variables..."
kubectl create secret generic cmbcluster-backend-secrets \
  --from-literal=SECRET_KEY="$SECRET_KEY" \
  --from-literal=GOOGLE_CLIENT_SECRET="$GOOGLE_CLIENT_SECRET" \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Generate Next.js auth secret if not provided
NEXTAUTH_SECRET=${NEXTAUTH_SECRET:-$(openssl rand -base64 32)}

# Create frontend secret
kubectl create secret generic cmbcluster-frontend-secrets \
  --from-literal=NEXTAUTH_SECRET="$NEXTAUTH_SECRET" \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Prepare Helm values
echo ""
echo "Preparing Helm values for deployment..."

# Create temporary values file for AWS-specific configuration
cat >/tmp/aws-values.yaml <<EOF
global:
  projectId: "$AWS_ACCOUNT_ID"
  clusterName: "$CLUSTER_NAME"
  registryUrl: "$ECR_URI"
  imageTag: "latest"
  cloudProvider: "aws"
  awsRegion: "$AWS_REGION"

workloadIdentity:
  iamRoleArn: "$IAM_ROLE_ARN"

serviceAccount:
  create: false
  name: "cmbcluster-ksa"

backend:
  image:
    repository: ${ECR_URI}/cmbcluster-backend
    tag: "latest"
  config:
    apiUrl: "https://api.${BASE_DOMAIN}"
    frontendUrl: "https://${BASE_DOMAIN}"
    googleClientId: "$GOOGLE_CLIENT_ID"
    cloudProvider: "aws"
    awsRegion: "$AWS_REGION"
    s3BucketDb: "${AWS_ACCOUNT_ID}-${CLUSTER_NAME}-db"
    s3BucketUserPrefix: "${AWS_ACCOUNT_ID}-${CLUSTER_NAME}-user"
  secretName: "cmbcluster-backend-secrets"

frontend:
  image:
    repository: ${ECR_URI}/cmbcluster-frontend
    tag: "latest"
  config:
    nextAuthUrl: "https://${BASE_DOMAIN}"
    apiUrl: "https://api.${BASE_DOMAIN}"

ingress:
  enabled: true
  className: "alb"
  clusterIssuer: "letsencrypt-prod"
  baseDomain: "$BASE_DOMAIN"
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: '30'
    alb.ingress.kubernetes.io/healthcheck-timeout-seconds: '5'
    alb.ingress.kubernetes.io/healthy-threshold-count: '2'
    alb.ingress.kubernetes.io/unhealthy-threshold-count: '3'
  tls:
    enabled: true

userEnvironment:
  image:
    repository: ${ECR_URI}/cmbcluster-user-env
    tag: "latest"
  serviceAccount:
    name: "cmbcluster-user-sa"
  storage:
    s3Enabled: true
    s3BucketPrefix: "${AWS_ACCOUNT_ID}-${CLUSTER_NAME}-user"
EOF

# Deploy with Helm
echo ""
echo "Deploying CMBCluster with Helm..."
helm upgrade --install cmbcluster ./helm \
  --namespace $NAMESPACE \
  --values /tmp/aws-values.yaml \
  --wait \
  --timeout 10m

rm /tmp/aws-values.yaml

# Wait for deployments to be ready
echo ""
echo "Waiting for deployments to be ready..."
kubectl rollout status deployment/cmbcluster-backend -n $NAMESPACE --timeout=5m
kubectl rollout status deployment/cmbcluster-frontend -n $NAMESPACE --timeout=5m

# Get ALB DNS name
echo ""
echo "Getting Application Load Balancer DNS name..."
sleep 10 # Give ALB time to provision
ALB_DNS=$(kubectl get ingress -n $NAMESPACE cmbcluster-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")

echo ""
echo "Deployment complete!"
echo ""
echo "Summary:"
echo "- Namespace: $NAMESPACE"
echo "- Backend: cmbcluster-backend"
echo "- Frontend: cmbcluster-frontend"
echo "- IAM Role: $IAM_ROLE_ARN"
echo ""
echo "Load Balancer:"
echo "- ALB DNS: $ALB_DNS"
echo ""
echo "Next steps:"
echo "1. Configure DNS records:"
echo "   - Create CNAME record: ${BASE_DOMAIN} -> $ALB_DNS"
echo "   - Create CNAME record: api.${BASE_DOMAIN} -> $ALB_DNS"
echo "   - Create CNAME record: *.${BASE_DOMAIN} -> $ALB_DNS"
echo ""
echo "2. Wait for DNS propagation (may take a few minutes)"
echo ""
echo "3. Verify deployment:"
echo "   kubectl get pods -n $NAMESPACE"
echo "   kubectl get ingress -n $NAMESPACE"
echo "   kubectl logs -f deployment/cmbcluster-backend -n $NAMESPACE"
echo ""
echo "4. Access your application:"
echo "   https://${BASE_DOMAIN}"
echo "   https://api.${BASE_DOMAIN}/docs"
echo ""
