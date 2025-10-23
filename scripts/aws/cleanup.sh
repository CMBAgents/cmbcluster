#!/bin/bash
set -e

# Configuration - should match setup-cluster-aws.sh for consistency
AWS_REGION=${1:-"us-east-1"}
EKS_CLUSTER_NAME=${2:-"cmbcluster-eks"}
AWS_ACCOUNT_ID=${3:-$(aws sts get-caller-identity --query Account --output text 2>/dev/null)}
CONFIRM=${4:-"no"}

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "Error: AWS_ACCOUNT_ID is required"
    echo "Usage: $0 [AWS_REGION] [EKS_CLUSTER_NAME] [AWS_ACCOUNT_ID] [yes]"
    exit 1
fi

# Define resource names based on conventions in setup-cluster-aws.sh
VPC_NAME="${EKS_CLUSTER_NAME}-vpc"
ECR_REPO_BACKEND="${EKS_CLUSTER_NAME}-backend"
ECR_REPO_FRONTEND="${EKS_CLUSTER_NAME}-frontend"
S3_DB_BUCKET="${EKS_CLUSTER_NAME}-db-${AWS_ACCOUNT_ID}"
S3_USER_BUCKET_PREFIX="${EKS_CLUSTER_NAME}-user"
IRSA_ROLE_NAME="${EKS_CLUSTER_NAME}-workload-role"
EKS_ROLE_NAME="${EKS_CLUSTER_NAME}-cluster-role"
NODE_ROLE_NAME="${EKS_CLUSTER_NAME}-node-role"
ALB_POLICY_NAME="${EKS_CLUSTER_NAME}-alb-policy"
S3_POLICY_NAME="${EKS_CLUSTER_NAME}-s3-policy"
HELM_RELEASE_NAME="cmbcluster"
K8S_NAMESPACE="cmbcluster"

if [ "$CONFIRM" != "yes" ]; then
    echo "⚠️ This will delete ALL CMBCluster AWS resources!"
    echo "This includes:"
    echo "- All user environments and data"
    echo "- The EKS cluster ($EKS_CLUSTER_NAME) and its node groups"
    echo "- All persistent volumes"
    echo "- All container images in ECR"
    echo "- NAT Gateway, Internet Gateway, VPC, and Subnets"
    echo "- S3 buckets (database and user buckets)"
    echo "- IAM roles and policies"
    echo "- Elastic IPs"
    echo ""
    read -p "Are you sure? Type 'yes' to continue: " CONFIRM
fi

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

echo "🧹 Cleaning up CMBCluster AWS resources..."

# Update kubeconfig to access the cluster
echo "🔑 Updating kubeconfig..."
aws eks update-kubeconfig --name $EKS_CLUSTER_NAME --region $AWS_REGION 2>/dev/null || echo "⚠️ Could not update kubeconfig"

# Delete Helm release
if helm status $HELM_RELEASE_NAME -n $K8S_NAMESPACE >/dev/null 2>&1; then
    echo "🗑️ Deleting Helm release '$HELM_RELEASE_NAME'..."
    helm uninstall $HELM_RELEASE_NAME -n $K8S_NAMESPACE --wait
else
    echo "✅ Helm release '$HELM_RELEASE_NAME' not found, skipping."
fi

# Delete namespace (this will delete all resources in it)
if kubectl get namespace $K8S_NAMESPACE >/dev/null 2>&1; then
    echo "🗑️ Deleting Kubernetes namespace '$K8S_NAMESPACE'..."
    kubectl delete namespace $K8S_NAMESPACE --wait=true
else
    echo "✅ Kubernetes namespace '$K8S_NAMESPACE' not found, skipping."
fi

# Delete AWS Load Balancer Controller
echo "🗑️ Deleting AWS Load Balancer Controller..."
helm uninstall aws-load-balancer-controller -n kube-system 2>/dev/null || echo "✅ ALB Controller not found"

# Delete service account for ALB controller
eksctl delete iamserviceaccount \
    --cluster=$EKS_CLUSTER_NAME \
    --namespace=kube-system \
    --name=aws-load-balancer-controller \
    --region=$AWS_REGION 2>/dev/null || echo "✅ ALB service account not found"

# Delete cert-manager
echo "🗑️ Deleting cert-manager..."
kubectl delete -f https://github.com/jetstack/cert-manager/releases/download/v1.13.0/cert-manager.yaml 2>/dev/null || echo "✅ cert-manager not found"

# Delete S3 CSI Driver
echo "🗑️ Deleting S3 CSI Driver..."
kubectl delete -k "github.com/awslabs/mountpoint-s3-csi-driver/deploy/kubernetes/overlays/stable/?ref=v1.5.0" 2>/dev/null || echo "✅ S3 CSI Driver not found"

# Delete EBS CSI Driver addon
echo "🗑️ Deleting EBS CSI Driver..."
aws eks delete-addon \
    --cluster-name $EKS_CLUSTER_NAME \
    --addon-name aws-ebs-csi-driver \
    --region $AWS_REGION 2>/dev/null || echo "✅ EBS CSI Driver not found"

# Delete Node Group
echo "🗑️ Deleting EKS node group (this may take a few minutes)..."
aws eks delete-nodegroup \
    --cluster-name $EKS_CLUSTER_NAME \
    --nodegroup-name "${EKS_CLUSTER_NAME}-nodes" \
    --region $AWS_REGION 2>/dev/null || echo "✅ Node group not found"

echo "⏳ Waiting for node group deletion..."
aws eks wait nodegroup-deleted \
    --cluster-name $EKS_CLUSTER_NAME \
    --nodegroup-name "${EKS_CLUSTER_NAME}-nodes" \
    --region $AWS_REGION 2>/dev/null || echo "✅ Node group already deleted"

# Delete EKS Cluster
echo "🗑️ Deleting EKS cluster (this may take 10-15 minutes)..."
aws eks delete-cluster \
    --name $EKS_CLUSTER_NAME \
    --region $AWS_REGION 2>/dev/null || echo "✅ EKS cluster not found"

echo "⏳ Waiting for cluster deletion..."
aws eks wait cluster-deleted \
    --name $EKS_CLUSTER_NAME \
    --region $AWS_REGION 2>/dev/null || echo "✅ Cluster already deleted"

# Get VPC ID
VPC_ID=$(aws ec2 describe-vpcs \
    --filters "Name=tag:Name,Values=$VPC_NAME" \
    --region $AWS_REGION \
    --query 'Vpcs[0].VpcId' \
    --output text 2>/dev/null)

if [ -z "$VPC_ID" ] || [ "$VPC_ID" == "None" ]; then
    echo "✅ VPC not found, skipping network cleanup"
else
    echo "🗑️ Found VPC: $VPC_ID"

    # Delete NAT Gateway
    NAT_GW_ID=$(aws ec2 describe-nat-gateways \
        --filter "Name=vpc-id,Values=$VPC_ID" "Name=state,Values=available" \
        --region $AWS_REGION \
        --query 'NatGateways[0].NatGatewayId' \
        --output text 2>/dev/null)

    if [ -n "$NAT_GW_ID" ] && [ "$NAT_GW_ID" != "None" ]; then
        echo "🗑️ Deleting NAT Gateway $NAT_GW_ID..."
        aws ec2 delete-nat-gateway --nat-gateway-id $NAT_GW_ID --region $AWS_REGION
        echo "⏳ Waiting for NAT Gateway deletion..."
        aws ec2 wait nat-gateway-deleted --nat-gateway-ids $NAT_GW_ID --region $AWS_REGION 2>/dev/null || echo "✅ NAT Gateway deleted"
    else
        echo "✅ NAT Gateway not found"
    fi

    # Release Elastic IPs
    echo "🗑️ Releasing Elastic IPs..."
    EIP_ALLOC_IDS=$(aws ec2 describe-addresses \
        --filters "Name=tag:Name,Values=${EKS_CLUSTER_NAME}-nat-eip-*" \
        --region $AWS_REGION \
        --query 'Addresses[].AllocationId' \
        --output text 2>/dev/null)

    for EIP_ID in $EIP_ALLOC_IDS; do
        if [ -n "$EIP_ID" ]; then
            echo "   - Releasing EIP $EIP_ID..."
            aws ec2 release-address --allocation-id $EIP_ID --region $AWS_REGION 2>/dev/null || echo "✅ EIP already released"
        fi
    done

    # Delete Internet Gateway
    IGW_ID=$(aws ec2 describe-internet-gateways \
        --filters "Name=attachment.vpc-id,Values=$VPC_ID" \
        --region $AWS_REGION \
        --query 'InternetGateways[0].InternetGatewayId' \
        --output text 2>/dev/null)

    if [ -n "$IGW_ID" ] && [ "$IGW_ID" != "None" ]; then
        echo "🗑️ Detaching and deleting Internet Gateway $IGW_ID..."
        aws ec2 detach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID --region $AWS_REGION 2>/dev/null || echo "✅ IGW already detached"
        aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID --region $AWS_REGION 2>/dev/null || echo "✅ IGW already deleted"
    else
        echo "✅ Internet Gateway not found"
    fi

    # Delete Subnets
    echo "🗑️ Deleting subnets..."
    SUBNET_IDS=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=$VPC_ID" \
        --region $AWS_REGION \
        --query 'Subnets[].SubnetId' \
        --output text 2>/dev/null)

    for SUBNET_ID in $SUBNET_IDS; do
        if [ -n "$SUBNET_ID" ]; then
            echo "   - Deleting subnet $SUBNET_ID..."
            aws ec2 delete-subnet --subnet-id $SUBNET_ID --region $AWS_REGION 2>/dev/null || echo "✅ Subnet already deleted"
        fi
    done

    # Delete Route Tables (except main)
    echo "🗑️ Deleting route tables..."
    RT_IDS=$(aws ec2 describe-route-tables \
        --filters "Name=vpc-id,Values=$VPC_ID" \
        --region $AWS_REGION \
        --query 'RouteTables[?Associations[0].Main!=`true`].RouteTableId' \
        --output text 2>/dev/null)

    for RT_ID in $RT_IDS; do
        if [ -n "$RT_ID" ]; then
            echo "   - Deleting route table $RT_ID..."
            aws ec2 delete-route-table --route-table-id $RT_ID --region $AWS_REGION 2>/dev/null || echo "✅ Route table already deleted"
        fi
    done

    # Delete Security Groups (except default)
    echo "🗑️ Deleting security groups..."
    SG_IDS=$(aws ec2 describe-security-groups \
        --filters "Name=vpc-id,Values=$VPC_ID" \
        --region $AWS_REGION \
        --query 'SecurityGroups[?GroupName!=`default`].GroupId' \
        --output text 2>/dev/null)

    for SG_ID in $SG_IDS; do
        if [ -n "$SG_ID" ]; then
            echo "   - Deleting security group $SG_ID..."
            aws ec2 delete-security-group --group-id $SG_ID --region $AWS_REGION 2>/dev/null || echo "✅ Security group already deleted"
        fi
    done

    # Delete VPC
    echo "🗑️ Deleting VPC $VPC_ID..."
    aws ec2 delete-vpc --vpc-id $VPC_ID --region $AWS_REGION 2>/dev/null || echo "✅ VPC already deleted"
fi

# Empty and delete S3 database bucket
echo "🗑️ Emptying and deleting S3 database bucket..."
aws s3 rb s3://$S3_DB_BUCKET --force --region $AWS_REGION 2>/dev/null || echo "✅ S3 database bucket not found or already deleted"

# Delete user S3 buckets
echo "🗑️ Deleting user S3 buckets..."
USER_BUCKETS=$(aws s3api list-buckets --query "Buckets[?starts_with(Name, '${S3_USER_BUCKET_PREFIX}')].Name" --output text 2>/dev/null)
for BUCKET in $USER_BUCKETS; do
    if [ -n "$BUCKET" ]; then
        echo "   - Deleting bucket $BUCKET..."
        aws s3 rb s3://$BUCKET --force --region $AWS_REGION 2>/dev/null || echo "✅ Bucket already deleted"
    fi
done

# Delete ECR repositories
echo "🗑️ Deleting ECR repositories..."
aws ecr delete-repository \
    --repository-name $ECR_REPO_BACKEND \
    --force \
    --region $AWS_REGION 2>/dev/null || echo "✅ Backend ECR repository not found"

aws ecr delete-repository \
    --repository-name $ECR_REPO_FRONTEND \
    --force \
    --region $AWS_REGION 2>/dev/null || echo "✅ Frontend ECR repository not found"

# Delete IAM roles and policies
echo "🗑️ Deleting IAM roles and policies..."

# Detach and delete IRSA role
echo "   - Deleting IRSA role $IRSA_ROLE_NAME..."
IRSA_POLICIES=$(aws iam list-attached-role-policies --role-name $IRSA_ROLE_NAME --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null)
for POLICY_ARN in $IRSA_POLICIES; do
    if [ -n "$POLICY_ARN" ]; then
        aws iam detach-role-policy --role-name $IRSA_ROLE_NAME --policy-arn $POLICY_ARN 2>/dev/null || echo "✅ Policy already detached"
    fi
done
aws iam delete-role --role-name $IRSA_ROLE_NAME --region $AWS_REGION 2>/dev/null || echo "✅ IRSA role not found"

# Detach and delete EKS cluster role
echo "   - Deleting EKS cluster role $EKS_ROLE_NAME..."
EKS_POLICIES=$(aws iam list-attached-role-policies --role-name $EKS_ROLE_NAME --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null)
for POLICY_ARN in $EKS_POLICIES; do
    if [ -n "$POLICY_ARN" ]; then
        aws iam detach-role-policy --role-name $EKS_ROLE_NAME --policy-arn $POLICY_ARN 2>/dev/null || echo "✅ Policy already detached"
    fi
done
aws iam delete-role --role-name $EKS_ROLE_NAME --region $AWS_REGION 2>/dev/null || echo "✅ EKS cluster role not found"

# Detach and delete node role
echo "   - Deleting node role $NODE_ROLE_NAME..."
NODE_POLICIES=$(aws iam list-attached-role-policies --role-name $NODE_ROLE_NAME --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null)
for POLICY_ARN in $NODE_POLICIES; do
    if [ -n "$POLICY_ARN" ]; then
        aws iam detach-role-policy --role-name $NODE_ROLE_NAME --policy-arn $POLICY_ARN 2>/dev/null || echo "✅ Policy already detached"
    fi
done
aws iam delete-role --role-name $NODE_ROLE_NAME --region $AWS_REGION 2>/dev/null || echo "✅ Node role not found"

# Delete custom policies
echo "   - Deleting custom policies..."
aws iam delete-policy \
    --policy-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${ALB_POLICY_NAME}" \
    --region $AWS_REGION 2>/dev/null || echo "✅ ALB policy not found"

aws iam delete-policy \
    --policy-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${S3_POLICY_NAME}" \
    --region $AWS_REGION 2>/dev/null || echo "✅ S3 policy not found"

echo "✅ Cleanup complete! Some resources like Route53 DNS records and Cognito user pools must be removed manually."
echo ""
echo "⚠️ Note: If you see errors about resources not found, they may have been already deleted or never created."
