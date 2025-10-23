#!/bin/bash
set -e

# --- Configuration Loading ---
# 1. Load defaults from .env file if it exists.
# 2. Allow overrides from command-line arguments.
# 3. Set final defaults for any remaining unset variables.

if [ -f .env ]; then
    echo "📝 Loading environment variables from .env file..."
    set -o allexport
    source .env
    set +o allexport
fi

# --- Variable Definitions & Precedence ---
# Command-line arguments override .env file values.
AWS_REGION=${1:-$AWS_REGION}
EKS_CLUSTER_NAME=${2:-$EKS_CLUSTER_NAME}
AWS_ACCOUNT_ID=${3:-$AWS_ACCOUNT_ID}

# Set final defaults if variables are still not set
AWS_REGION=${AWS_REGION:-"us-east-1"}
EKS_CLUSTER_NAME=${EKS_CLUSTER_NAME:-"cmbcluster-eks"}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text 2>/dev/null)}

# Validate required variables
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "Error: AWS_ACCOUNT_ID is required. Set it in .env, pass as argument, or configure AWS CLI."
    echo "Usage: $0 [AWS_REGION] [EKS_CLUSTER_NAME] [AWS_ACCOUNT_ID]"
    exit 1
fi

echo "🚀 Setting up CMBCluster AWS EKS infrastructure..."
echo "--------------------------------------------------"
echo "AWS Account:  $AWS_ACCOUNT_ID"
echo "AWS Region:   $AWS_REGION"
echo "EKS Cluster:  $EKS_CLUSTER_NAME"
echo "--------------------------------------------------"

# Set up infrastructure variables
VPC_NAME="${EKS_CLUSTER_NAME}-vpc"
ECR_REPO_BACKEND="${EKS_CLUSTER_NAME}-backend"
ECR_REPO_FRONTEND="${EKS_CLUSTER_NAME}-frontend"
S3_DB_BUCKET="${EKS_CLUSTER_NAME}-db-${AWS_ACCOUNT_ID}"
S3_USER_BUCKET_PREFIX="${EKS_CLUSTER_NAME}-user"
IRSA_ROLE_NAME="${EKS_CLUSTER_NAME}-workload-role"

# Network CIDR ranges from .env (with fallback defaults)
VPC_CIDR=${VPC_CIDR:-"10.0.0.0/16"}
PUBLIC_SUBNET_1_CIDR=${PUBLIC_SUBNET_1_CIDR:-"10.0.1.0/24"}
PUBLIC_SUBNET_2_CIDR=${PUBLIC_SUBNET_2_CIDR:-"10.0.2.0/24"}
PUBLIC_SUBNET_3_CIDR=${PUBLIC_SUBNET_3_CIDR:-"10.0.3.0/24"}
PRIVATE_SUBNET_1_CIDR=${PRIVATE_SUBNET_1_CIDR:-"10.0.11.0/24"}
PRIVATE_SUBNET_2_CIDR=${PRIVATE_SUBNET_2_CIDR:-"10.0.12.0/24"}
PRIVATE_SUBNET_3_CIDR=${PRIVATE_SUBNET_3_CIDR:-"10.0.13.0/24"}

# Get availability zones
echo "🌐 Getting availability zones for region $AWS_REGION..."
AZ_1=$(aws ec2 describe-availability-zones --region $AWS_REGION --query 'AvailabilityZones[0].ZoneName' --output text)
AZ_2=$(aws ec2 describe-availability-zones --region $AWS_REGION --query 'AvailabilityZones[1].ZoneName' --output text)
AZ_3=$(aws ec2 describe-availability-zones --region $AWS_REGION --query 'AvailabilityZones[2].ZoneName' --output text)

echo "Using AZs: $AZ_1, $AZ_2, $AZ_3"

# Create VPC
echo "🌐 Creating VPC..."
VPC_ID=$(aws ec2 create-vpc \
    --cidr-block $VPC_CIDR \
    --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=$VPC_NAME},{Key=kubernetes.io/cluster/$EKS_CLUSTER_NAME,Value=shared}]" \
    --region $AWS_REGION \
    --query 'Vpc.VpcId' \
    --output text 2>/dev/null || aws ec2 describe-vpcs \
    --filters "Name=tag:Name,Values=$VPC_NAME" \
    --region $AWS_REGION \
    --query 'Vpcs[0].VpcId' \
    --output text)

if [ -z "$VPC_ID" ] || [ "$VPC_ID" == "None" ]; then
    echo "❌ Failed to create or find VPC"
    exit 1
fi

echo "✅ VPC created/found: $VPC_ID"

# Enable DNS hostname support
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames --region $AWS_REGION
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support --region $AWS_REGION

# Create Internet Gateway
echo "🌐 Creating Internet Gateway..."
IGW_ID=$(aws ec2 create-internet-gateway \
    --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=${EKS_CLUSTER_NAME}-igw}]" \
    --region $AWS_REGION \
    --query 'InternetGateway.InternetGatewayId' \
    --output text 2>/dev/null || aws ec2 describe-internet-gateways \
    --filters "Name=tag:Name,Values=${EKS_CLUSTER_NAME}-igw" \
    --region $AWS_REGION \
    --query 'InternetGateways[0].InternetGatewayId' \
    --output text)

echo "✅ Internet Gateway: $IGW_ID"

# Attach IGW to VPC
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID --region $AWS_REGION 2>/dev/null || echo "✅ IGW already attached"

# Create Public Subnets
echo "🔗 Creating public subnets..."
PUBLIC_SUBNET_1_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block $PUBLIC_SUBNET_1_CIDR \
    --availability-zone $AZ_1 \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${EKS_CLUSTER_NAME}-public-1},{Key=kubernetes.io/cluster/$EKS_CLUSTER_NAME,Value=shared},{Key=kubernetes.io/role/elb,Value=1}]" \
    --region $AWS_REGION \
    --query 'Subnet.SubnetId' \
    --output text 2>/dev/null || aws ec2 describe-subnets \
    --filters "Name=tag:Name,Values=${EKS_CLUSTER_NAME}-public-1" \
    --region $AWS_REGION \
    --query 'Subnets[0].SubnetId' \
    --output text)

PUBLIC_SUBNET_2_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block $PUBLIC_SUBNET_2_CIDR \
    --availability-zone $AZ_2 \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${EKS_CLUSTER_NAME}-public-2},{Key=kubernetes.io/cluster/$EKS_CLUSTER_NAME,Value=shared},{Key=kubernetes.io/role/elb,Value=1}]" \
    --region $AWS_REGION \
    --query 'Subnet.SubnetId' \
    --output text 2>/dev/null || aws ec2 describe-subnets \
    --filters "Name=tag:Name,Values=${EKS_CLUSTER_NAME}-public-2" \
    --region $AWS_REGION \
    --query 'Subnets[0].SubnetId' \
    --output text)

PUBLIC_SUBNET_3_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block $PUBLIC_SUBNET_3_CIDR \
    --availability-zone $AZ_3 \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${EKS_CLUSTER_NAME}-public-3},{Key=kubernetes.io/cluster/$EKS_CLUSTER_NAME,Value=shared},{Key=kubernetes.io/role/elb,Value=1}]" \
    --region $AWS_REGION \
    --query 'Subnet.SubnetId' \
    --output text 2>/dev/null || aws ec2 describe-subnets \
    --filters "Name=tag:Name,Values=${EKS_CLUSTER_NAME}-public-3" \
    --region $AWS_REGION \
    --query 'Subnets[0].SubnetId' \
    --output text)

echo "✅ Public Subnets: $PUBLIC_SUBNET_1_ID, $PUBLIC_SUBNET_2_ID, $PUBLIC_SUBNET_3_ID"

# Enable auto-assign public IP on public subnets
aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET_1_ID --map-public-ip-on-launch --region $AWS_REGION
aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET_2_ID --map-public-ip-on-launch --region $AWS_REGION
aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET_3_ID --map-public-ip-on-launch --region $AWS_REGION

# Create Private Subnets
echo "🔗 Creating private subnets..."
PRIVATE_SUBNET_1_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block $PRIVATE_SUBNET_1_CIDR \
    --availability-zone $AZ_1 \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${EKS_CLUSTER_NAME}-private-1},{Key=kubernetes.io/cluster/$EKS_CLUSTER_NAME,Value=shared},{Key=kubernetes.io/role/internal-elb,Value=1}]" \
    --region $AWS_REGION \
    --query 'Subnet.SubnetId' \
    --output text 2>/dev/null || aws ec2 describe-subnets \
    --filters "Name=tag:Name,Values=${EKS_CLUSTER_NAME}-private-1" \
    --region $AWS_REGION \
    --query 'Subnets[0].SubnetId' \
    --output text)

PRIVATE_SUBNET_2_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block $PRIVATE_SUBNET_2_CIDR \
    --availability-zone $AZ_2 \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${EKS_CLUSTER_NAME}-private-2},{Key=kubernetes.io/cluster/$EKS_CLUSTER_NAME,Value=shared},{Key=kubernetes.io/role/internal-elb,Value=1}]" \
    --region $AWS_REGION \
    --query 'Subnet.SubnetId' \
    --output text 2>/dev/null || aws ec2 describe-subnets \
    --filters "Name=tag:Name,Values=${EKS_CLUSTER_NAME}-private-2" \
    --region $AWS_REGION \
    --query 'Subnets[0].SubnetId' \
    --output text)

PRIVATE_SUBNET_3_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block $PRIVATE_SUBNET_3_CIDR \
    --availability-zone $AZ_3 \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${EKS_CLUSTER_NAME}-private-3},{Key=kubernetes.io/cluster/$EKS_CLUSTER_NAME,Value=shared},{Key=kubernetes.io/role/internal-elb,Value=1}]" \
    --region $AWS_REGION \
    --query 'Subnet.SubnetId' \
    --output text 2>/dev/null || aws ec2 describe-subnets \
    --filters "Name=tag:Name,Values=${EKS_CLUSTER_NAME}-private-3" \
    --region $AWS_REGION \
    --query 'Subnets[0].SubnetId' \
    --output text)

echo "✅ Private Subnets: $PRIVATE_SUBNET_1_ID, $PRIVATE_SUBNET_2_ID, $PRIVATE_SUBNET_3_ID"

# Create public route table
echo "🛣️ Creating public route table..."
PUBLIC_RT_ID=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${EKS_CLUSTER_NAME}-public-rt}]" \
    --region $AWS_REGION \
    --query 'RouteTable.RouteTableId' \
    --output text 2>/dev/null || aws ec2 describe-route-tables \
    --filters "Name=tag:Name,Values=${EKS_CLUSTER_NAME}-public-rt" \
    --region $AWS_REGION \
    --query 'RouteTables[0].RouteTableId' \
    --output text)

echo "✅ Public Route Table: $PUBLIC_RT_ID"

# Add route to internet gateway
aws ec2 create-route --route-table-id $PUBLIC_RT_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID --region $AWS_REGION 2>/dev/null || echo "✅ Route already exists"

# Associate public subnets with public route table
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET_1_ID --route-table-id $PUBLIC_RT_ID --region $AWS_REGION 2>/dev/null || echo "✅ Subnet 1 already associated"
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET_2_ID --route-table-id $PUBLIC_RT_ID --region $AWS_REGION 2>/dev/null || echo "✅ Subnet 2 already associated"
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET_3_ID --route-table-id $PUBLIC_RT_ID --region $AWS_REGION 2>/dev/null || echo "✅ Subnet 3 already associated"

# Create Elastic IPs for NAT Gateways
echo "🌍 Creating Elastic IPs for NAT Gateways..."
EIP_1_ALLOC_ID=$(aws ec2 allocate-address \
    --domain vpc \
    --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=${EKS_CLUSTER_NAME}-nat-eip-1}]" \
    --region $AWS_REGION \
    --query 'AllocationId' \
    --output text 2>/dev/null || aws ec2 describe-addresses \
    --filters "Name=tag:Name,Values=${EKS_CLUSTER_NAME}-nat-eip-1" \
    --region $AWS_REGION \
    --query 'Addresses[0].AllocationId' \
    --output text)

echo "✅ EIP 1: $EIP_1_ALLOC_ID"

# Create NAT Gateway in public subnet 1
echo "🌍 Creating NAT Gateway..."
NAT_GW_ID=$(aws ec2 create-nat-gateway \
    --subnet-id $PUBLIC_SUBNET_1_ID \
    --allocation-id $EIP_1_ALLOC_ID \
    --tag-specifications "ResourceType=natgateway,Tags=[{Key=Name,Value=${EKS_CLUSTER_NAME}-nat-gw}]" \
    --region $AWS_REGION \
    --query 'NatGateway.NatGatewayId' \
    --output text 2>/dev/null || aws ec2 describe-nat-gateways \
    --filter "Name=tag:Name,Values=${EKS_CLUSTER_NAME}-nat-gw" \
    --region $AWS_REGION \
    --query 'NatGateways[?State!=`deleted`]|[0].NatGatewayId' \
    --output text)

echo "✅ NAT Gateway: $NAT_GW_ID"
echo "⏳ Waiting for NAT Gateway to become available..."
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_ID --region $AWS_REGION

# Create private route table
echo "🛣️ Creating private route table..."
PRIVATE_RT_ID=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${EKS_CLUSTER_NAME}-private-rt}]" \
    --region $AWS_REGION \
    --query 'RouteTable.RouteTableId' \
    --output text 2>/dev/null || aws ec2 describe-route-tables \
    --filters "Name=tag:Name,Values=${EKS_CLUSTER_NAME}-private-rt" \
    --region $AWS_REGION \
    --query 'RouteTables[0].RouteTableId' \
    --output text)

echo "✅ Private Route Table: $PRIVATE_RT_ID"

# Add route to NAT gateway
aws ec2 create-route --route-table-id $PRIVATE_RT_ID --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GW_ID --region $AWS_REGION 2>/dev/null || echo "✅ Route already exists"

# Associate private subnets with private route table
aws ec2 associate-route-table --subnet-id $PRIVATE_SUBNET_1_ID --route-table-id $PRIVATE_RT_ID --region $AWS_REGION 2>/dev/null || echo "✅ Subnet 1 already associated"
aws ec2 associate-route-table --subnet-id $PRIVATE_SUBNET_2_ID --route-table-id $PRIVATE_RT_ID --region $AWS_REGION 2>/dev/null || echo "✅ Subnet 2 already associated"
aws ec2 associate-route-table --subnet-id $PRIVATE_SUBNET_3_ID --route-table-id $PRIVATE_RT_ID --region $AWS_REGION 2>/dev/null || echo "✅ Subnet 3 already associated"

# Create EKS Cluster IAM Role
echo "🔑 Creating EKS cluster IAM role..."
cat > /tmp/eks-cluster-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "eks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

EKS_ROLE_NAME="${EKS_CLUSTER_NAME}-cluster-role"
aws iam create-role \
    --role-name $EKS_ROLE_NAME \
    --assume-role-policy-document file:///tmp/eks-cluster-trust-policy.json \
    --region $AWS_REGION 2>/dev/null || echo "✅ EKS cluster role already exists"

aws iam attach-role-policy \
    --role-name $EKS_ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy \
    --region $AWS_REGION 2>/dev/null || echo "✅ Policy already attached"

EKS_ROLE_ARN=$(aws iam get-role --role-name $EKS_ROLE_NAME --query 'Role.Arn' --output text)
echo "✅ EKS Cluster Role: $EKS_ROLE_ARN"

# Create EKS Cluster
echo "🏗️ Creating EKS cluster (this may take 10-15 minutes)..."
aws eks create-cluster \
    --name $EKS_CLUSTER_NAME \
    --role-arn $EKS_ROLE_ARN \
    --resources-vpc-config subnetIds=$PRIVATE_SUBNET_1_ID,$PRIVATE_SUBNET_2_ID,$PRIVATE_SUBNET_3_ID,$PUBLIC_SUBNET_1_ID,$PUBLIC_SUBNET_2_ID,$PUBLIC_SUBNET_3_ID,endpointPublicAccess=true,endpointPrivateAccess=true \
    --region $AWS_REGION 2>/dev/null || echo "✅ EKS cluster already exists"

echo "⏳ Waiting for EKS cluster to become active..."
aws eks wait cluster-active --name $EKS_CLUSTER_NAME --region $AWS_REGION

# Update kubeconfig
echo "🔑 Updating kubeconfig..."
aws eks update-kubeconfig --name $EKS_CLUSTER_NAME --region $AWS_REGION

# Create Node Group IAM Role
echo "🔑 Creating node group IAM role..."
cat > /tmp/node-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

NODE_ROLE_NAME="${EKS_CLUSTER_NAME}-node-role"
aws iam create-role \
    --role-name $NODE_ROLE_NAME \
    --assume-role-policy-document file:///tmp/node-trust-policy.json \
    --region $AWS_REGION 2>/dev/null || echo "✅ Node role already exists"

# Attach required policies to node role
aws iam attach-role-policy --role-name $NODE_ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy 2>/dev/null || echo "✅ Policy attached"
aws iam attach-role-policy --role-name $NODE_ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy 2>/dev/null || echo "✅ Policy attached"
aws iam attach-role-policy --role-name $NODE_ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly 2>/dev/null || echo "✅ Policy attached"
aws iam attach-role-policy --role-name $NODE_ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AmazonEBSCSIDriverPolicy 2>/dev/null || echo "✅ Policy attached"

NODE_ROLE_ARN=$(aws iam get-role --role-name $NODE_ROLE_NAME --query 'Role.Arn' --output text)
echo "✅ Node Role: $NODE_ROLE_ARN"

# Create Node Group
echo "🖥️ Creating EKS node group..."
aws eks create-nodegroup \
    --cluster-name $EKS_CLUSTER_NAME \
    --nodegroup-name "${EKS_CLUSTER_NAME}-nodes" \
    --node-role $NODE_ROLE_ARN \
    --subnets $PRIVATE_SUBNET_1_ID $PRIVATE_SUBNET_2_ID $PRIVATE_SUBNET_3_ID \
    --scaling-config minSize=1,maxSize=3,desiredSize=2 \
    --instance-types t3.medium \
    --disk-size 50 \
    --region $AWS_REGION 2>/dev/null || echo "✅ Node group already exists"

echo "⏳ Waiting for node group to become active..."
aws eks wait nodegroup-active --cluster-name $EKS_CLUSTER_NAME --nodegroup-name "${EKS_CLUSTER_NAME}-nodes" --region $AWS_REGION

# Verify cluster access
echo "🔍 Verifying cluster access..."
kubectl get nodes

# Install EBS CSI Driver
echo "💾 Installing EBS CSI Driver..."
aws eks create-addon \
    --cluster-name $EKS_CLUSTER_NAME \
    --addon-name aws-ebs-csi-driver \
    --region $AWS_REGION 2>/dev/null || echo "✅ EBS CSI Driver already installed"

# Install S3 CSI Driver
echo "💾 Installing Mountpoint for S3 CSI Driver..."
kubectl apply -k "github.com/awslabs/mountpoint-s3-csi-driver/deploy/kubernetes/overlays/stable/?ref=v1.5.0" || echo "✅ S3 CSI Driver already installed"

# Install AWS Load Balancer Controller
echo "🌐 Installing AWS Load Balancer Controller..."

# Create IAM policy for ALB controller
cat > /tmp/alb-iam-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateServiceLinkedRole"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "iam:AWSServiceName": "elasticloadbalancing.amazonaws.com"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeAccountAttributes",
        "ec2:DescribeAddresses",
        "ec2:DescribeAvailabilityZones",
        "ec2:DescribeInternetGateways",
        "ec2:DescribeVpcs",
        "ec2:DescribeVpcPeeringConnections",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeInstances",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeTags",
        "ec2:GetCoipPoolUsage",
        "ec2:DescribeCoipPools",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeLoadBalancerAttributes",
        "elasticloadbalancing:DescribeListeners",
        "elasticloadbalancing:DescribeListenerCertificates",
        "elasticloadbalancing:DescribeSSLPolicies",
        "elasticloadbalancing:DescribeRules",
        "elasticloadbalancing:DescribeTargetGroups",
        "elasticloadbalancing:DescribeTargetGroupAttributes",
        "elasticloadbalancing:DescribeTargetHealth",
        "elasticloadbalancing:DescribeTags"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:DescribeUserPoolClient",
        "acm:ListCertificates",
        "acm:DescribeCertificate",
        "iam:ListServerCertificates",
        "iam:GetServerCertificate",
        "waf-regional:GetWebACL",
        "waf-regional:GetWebACLForResource",
        "waf-regional:AssociateWebACL",
        "waf-regional:DisassociateWebACL",
        "wafv2:GetWebACL",
        "wafv2:GetWebACLForResource",
        "wafv2:AssociateWebACL",
        "wafv2:DisassociateWebACL",
        "shield:GetSubscriptionState",
        "shield:DescribeProtection",
        "shield:CreateProtection",
        "shield:DeleteProtection"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:CreateSecurityGroup"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateTags"
      ],
      "Resource": "arn:aws:ec2:*:*:security-group/*",
      "Condition": {
        "StringEquals": {
          "ec2:CreateAction": "CreateSecurityGroup"
        },
        "Null": {
          "aws:RequestTag/elbv2.k8s.aws/cluster": "false"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateTags",
        "ec2:DeleteTags"
      ],
      "Resource": "arn:aws:ec2:*:*:security-group/*",
      "Condition": {
        "Null": {
          "aws:RequestTag/elbv2.k8s.aws/cluster": "true",
          "aws:ResourceTag/elbv2.k8s.aws/cluster": "false"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:DeleteSecurityGroup"
      ],
      "Resource": "*",
      "Condition": {
        "Null": {
          "aws:ResourceTag/elbv2.k8s.aws/cluster": "false"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:CreateLoadBalancer",
        "elasticloadbalancing:CreateTargetGroup"
      ],
      "Resource": "*",
      "Condition": {
        "Null": {
          "aws:RequestTag/elbv2.k8s.aws/cluster": "false"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:CreateListener",
        "elasticloadbalancing:DeleteListener",
        "elasticloadbalancing:CreateRule",
        "elasticloadbalancing:DeleteRule"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:AddTags",
        "elasticloadbalancing:RemoveTags"
      ],
      "Resource": [
        "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*",
        "arn:aws:elasticloadbalancing:*:*:loadbalancer/net/*/*",
        "arn:aws:elasticloadbalancing:*:*:loadbalancer/app/*/*"
      ],
      "Condition": {
        "Null": {
          "aws:RequestTag/elbv2.k8s.aws/cluster": "true",
          "aws:ResourceTag/elbv2.k8s.aws/cluster": "false"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:AddTags",
        "elasticloadbalancing:RemoveTags"
      ],
      "Resource": [
        "arn:aws:elasticloadbalancing:*:*:listener/net/*/*/*",
        "arn:aws:elasticloadbalancing:*:*:listener/app/*/*/*",
        "arn:aws:elasticloadbalancing:*:*:listener-rule/net/*/*/*",
        "arn:aws:elasticloadbalancing:*:*:listener-rule/app/*/*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:ModifyLoadBalancerAttributes",
        "elasticloadbalancing:SetIpAddressType",
        "elasticloadbalancing:SetSecurityGroups",
        "elasticloadbalancing:SetSubnets",
        "elasticloadbalancing:DeleteLoadBalancer",
        "elasticloadbalancing:ModifyTargetGroup",
        "elasticloadbalancing:ModifyTargetGroupAttributes",
        "elasticloadbalancing:DeleteTargetGroup"
      ],
      "Resource": "*",
      "Condition": {
        "Null": {
          "aws:ResourceTag/elbv2.k8s.aws/cluster": "false"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:RegisterTargets",
        "elasticloadbalancing:DeregisterTargets"
      ],
      "Resource": "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:SetWebAcl",
        "elasticloadbalancing:ModifyListener",
        "elasticloadbalancing:AddListenerCertificates",
        "elasticloadbalancing:RemoveListenerCertificates",
        "elasticloadbalancing:ModifyRule"
      ],
      "Resource": "*"
    }
  ]
}
EOF

ALB_POLICY_NAME="${EKS_CLUSTER_NAME}-alb-policy"
aws iam create-policy \
    --policy-name $ALB_POLICY_NAME \
    --policy-document file:///tmp/alb-iam-policy.json \
    --region $AWS_REGION 2>/dev/null || echo "✅ ALB IAM policy already exists"

ALB_POLICY_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${ALB_POLICY_NAME}"

# Create IAM role for ALB controller using IRSA
eksctl create iamserviceaccount \
    --cluster=$EKS_CLUSTER_NAME \
    --namespace=kube-system \
    --name=aws-load-balancer-controller \
    --attach-policy-arn=$ALB_POLICY_ARN \
    --override-existing-serviceaccounts \
    --region=$AWS_REGION \
    --approve 2>/dev/null || echo "✅ Service account already exists"

# Install ALB controller via Helm
helm repo add eks https://aws.github.io/eks-charts 2>/dev/null || echo "✅ Repo already added"
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
    -n kube-system \
    --set clusterName=$EKS_CLUSTER_NAME \
    --set serviceAccount.create=false \
    --set serviceAccount.name=aws-load-balancer-controller \
    --set region=$AWS_REGION \
    --set vpcId=$VPC_ID 2>/dev/null || echo "✅ ALB Controller already installed"

# Install cert-manager for SSL certificates
echo "🔒 Installing cert-manager..."
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.13.0/cert-manager.yaml 2>/dev/null || echo "✅ cert-manager already installed"

echo "⏳ Waiting for cert-manager to be ready..."
kubectl wait --namespace cert-manager \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/instance=cert-manager \
    --timeout=300s 2>/dev/null || echo "✅ cert-manager already ready"

if [ -z "$LETSENCRYPT_EMAIL" ] || [ "$LETSENCRYPT_EMAIL" == "your-email@example.com" ]; then
    echo "❌ Error: LETSENCRYPT_EMAIL is not set or is the default value."
    echo "Please set a valid email in your .env file for Let's Encrypt notifications."
    exit 1
fi

# Create ClusterIssuer for Let's Encrypt
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

# Create ECR repositories
echo "📦 Creating ECR repositories..."
aws ecr create-repository \
    --repository-name $ECR_REPO_BACKEND \
    --region $AWS_REGION 2>/dev/null || echo "✅ Backend ECR repository already exists"

aws ecr create-repository \
    --repository-name $ECR_REPO_FRONTEND \
    --region $AWS_REGION 2>/dev/null || echo "✅ Frontend ECR repository already exists"

ECR_REGISTRY_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
echo "✅ ECR Registry URL: $ECR_REGISTRY_URL"

# Create S3 bucket for database
echo "🪣 Creating S3 bucket for database..."
aws s3api create-bucket \
    --bucket $S3_DB_BUCKET \
    --region $AWS_REGION \
    --create-bucket-configuration LocationConstraint=$AWS_REGION 2>/dev/null || echo "✅ S3 database bucket already exists"

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket $S3_DB_BUCKET \
    --versioning-configuration Status=Enabled \
    --region $AWS_REGION

echo "✅ S3 bucket '$S3_DB_BUCKET' created with versioning enabled"

# Create IAM role for workload (IRSA)
echo "🔑 Creating IRSA role for workload..."
cat > /tmp/irsa-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/oidc.eks.${AWS_REGION}.amazonaws.com/id/$(aws eks describe-cluster --name $EKS_CLUSTER_NAME --region $AWS_REGION --query 'cluster.identity.oidc.issuer' --output text | cut -d '/' -f 5)"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.${AWS_REGION}.amazonaws.com/id/$(aws eks describe-cluster --name $EKS_CLUSTER_NAME --region $AWS_REGION --query 'cluster.identity.oidc.issuer' --output text | cut -d '/' -f 5):sub": "system:serviceaccount:default:cmbcluster-ksa"
        }
      }
    }
  ]
}
EOF

# Enable OIDC provider for EKS cluster
eksctl utils associate-iam-oidc-provider \
    --cluster $EKS_CLUSTER_NAME \
    --region $AWS_REGION \
    --approve 2>/dev/null || echo "✅ OIDC provider already associated"

aws iam create-role \
    --role-name $IRSA_ROLE_NAME \
    --assume-role-policy-document file:///tmp/irsa-trust-policy.json \
    --region $AWS_REGION 2>/dev/null || echo "✅ IRSA role already exists"

# Create and attach S3 policy for workload
cat > /tmp/s3-workload-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:GetObjectVersion",
        "s3:ListBucketVersions"
      ],
      "Resource": [
        "arn:aws:s3:::${S3_DB_BUCKET}",
        "arn:aws:s3:::${S3_DB_BUCKET}/*",
        "arn:aws:s3:::${S3_USER_BUCKET_PREFIX}-*",
        "arn:aws:s3:::${S3_USER_BUCKET_PREFIX}-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:ListAllMyBuckets"
      ],
      "Resource": "*"
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

S3_POLICY_NAME="${EKS_CLUSTER_NAME}-s3-policy"
aws iam create-policy \
    --policy-name $S3_POLICY_NAME \
    --policy-document file:///tmp/s3-workload-policy.json \
    --region $AWS_REGION 2>/dev/null || echo "✅ S3 policy already exists"

S3_POLICY_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${S3_POLICY_NAME}"

aws iam attach-role-policy \
    --role-name $IRSA_ROLE_NAME \
    --policy-arn $S3_POLICY_ARN 2>/dev/null || echo "✅ S3 policy already attached"

IRSA_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${IRSA_ROLE_NAME}"

echo "✅ AWS CMBCluster infrastructure setup complete!"
echo ""
echo "📋 Summary:"
echo "- VPC: $VPC_ID ($VPC_CIDR)"
echo "- EKS Cluster: $EKS_CLUSTER_NAME"
echo "- Region: $AWS_REGION"
echo "- ECR Registry: $ECR_REGISTRY_URL"
echo "- S3 Database Bucket: $S3_DB_BUCKET"
echo "- S3 User Bucket Prefix: ${S3_USER_BUCKET_PREFIX}-*"
echo "- IRSA Role: $IRSA_ROLE_ARN"
echo ""
echo "📝 Next steps:"
echo "1. Configure your domain DNS to point to the ALB ingress"
echo "2. Set up AWS Cognito user pool (or keep Google OAuth)"
echo "3. Ensure your Helm chart uses the Kubernetes Service Account 'cmbcluster-ksa' annotated with 'eks.amazonaws.com/role-arn=$IRSA_ROLE_ARN'"
echo "4. Run: ./scripts/deploy-aws.sh"
echo ""
echo "🔍 Useful commands:"
echo "kubectl get nodes"
echo "kubectl get service -A"
echo "aws eks describe-cluster --name $EKS_CLUSTER_NAME --region $AWS_REGION"

# Clean up temporary files
rm -f /tmp/eks-cluster-trust-policy.json /tmp/node-trust-policy.json /tmp/alb-iam-policy.json /tmp/irsa-trust-policy.json /tmp/s3-workload-policy.json
