#!/bin/bash
set -e

# Configuration
PROJECT_ID=${1:-$(gcloud config get-value project)}
CLUSTER_NAME=${2:-"cmbcluster"}
REGION=${3:-"us-central1"}
ZONE=${4:-"us-central1-b"}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is required"
    echo "Usage: $0 <PROJECT_ID> [CLUSTER_NAME] [REGION] [ZONE]"
    exit 1
fi

echo "🚀 Setting up CMBCluster private GKE infrastructure..."
echo "Project: $PROJECT_ID"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "Zone: $ZONE"

# Get current external IP for master authorized networks
echo "🌐 Getting current external IP for authorized networks..."
MY_IP=$(curl -s ifconfig.me)
echo "Current IP: $MY_IP"

# Set up network variables
NETWORK_NAME="${CLUSTER_NAME}-network"
SUBNET_NAME="${CLUSTER_NAME}-subnet"
PODS_RANGE="${CLUSTER_NAME}-pods"
SERVICES_RANGE="${CLUSTER_NAME}-services"
ROUTER_NAME="${CLUSTER_NAME}-nat-router"
NAT_NAME="${CLUSTER_NAME}-nat-config"

# Set the default project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📡 Enabling required APIs..."
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Create VPC network if not exists
if ! gcloud compute networks describe $NETWORK_NAME --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "🌐 Creating VPC network $NETWORK_NAME..."
    gcloud compute networks create $NETWORK_NAME \
        --subnet-mode=custom \
        --project=$PROJECT_ID
else
    echo "✅ VPC network $NETWORK_NAME already exists"
fi

# Create subnet with secondary ranges if not exists
if ! gcloud compute networks subnets describe $SUBNET_NAME --region=$REGION --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "🔗 Creating subnet $SUBNET_NAME with secondary ranges..."
    gcloud compute networks subnets create $SUBNET_NAME \
        --network=$NETWORK_NAME \
        --region=$REGION \
        --range=10.0.0.0/16 \
        --secondary-range $PODS_RANGE=10.1.0.0/16,$SERVICES_RANGE=10.2.0.0/20 \
        --enable-private-ip-google-access \
        --project=$PROJECT_ID
else
    echo "✅ Subnet $SUBNET_NAME already exists"
fi

# Create firewall rules for internal communication
echo "🔥 Creating firewall rules..."

# Allow internal communication within the subnet
gcloud compute firewall-rules create ${CLUSTER_NAME}-allow-internal \
    --network=$NETWORK_NAME \
    --allow=tcp,udp,icmp \
    --source-ranges=10.0.0.0/8 \
    --project=$PROJECT_ID \
    --quiet || echo "Firewall rule already exists"

# Allow Google health checks
gcloud compute firewall-rules create ${CLUSTER_NAME}-allow-health-checks \
    --network=$NETWORK_NAME \
    --allow=tcp \
    --source-ranges=130.211.0.0/22,35.191.0.0/16 \
    --target-tags=gke-node \
    --project=$PROJECT_ID \
    --quiet || echo "Health check firewall rule already exists"

# Create private GKE cluster
echo "🏗️ Creating private GKE cluster..."
if ! gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE --project=$PROJECT_ID >/dev/null 2>&1; then
    gcloud container clusters create $CLUSTER_NAME \
        --project=$PROJECT_ID \
        --zone=$ZONE \
        --network=$NETWORK_NAME \
        --subnetwork=$SUBNET_NAME \
        --cluster-secondary-range-name=$PODS_RANGE \
        --services-secondary-range-name=$SERVICES_RANGE \
        --enable-ip-alias \
        --enable-private-nodes \
        --master-ipv4-cidr=172.16.0.0/28 \
        --enable-master-authorized-networks \
        --master-authorized-networks $MY_IP/32 \
        --num-nodes=3 \
        --machine-type=n1-standard-2 \
        --disk-size=50GB \
        --disk-type=pd-standard \
        --enable-autorepair \
        --enable-autoupgrade \
        --enable-autoscaling \
        --min-nodes=1 \
        --max-nodes=10 \
        --enable-network-policy \
        --workload-pool=$PROJECT_ID.svc.id.goog \
        --addons=HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver \
        --logging=SYSTEM,WORKLOAD \
        --monitoring=SYSTEM
else
    echo "✅ Cluster $CLUSTER_NAME already exists"
fi

# Create Cloud Router for NAT if not exists
if ! gcloud compute routers describe $ROUTER_NAME --region=$REGION --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "🔄 Creating Cloud Router $ROUTER_NAME..."
    gcloud compute routers create $ROUTER_NAME \
        --network=$NETWORK_NAME \
        --region=$REGION \
        --project=$PROJECT_ID
else
    echo "✅ Cloud Router $ROUTER_NAME already exists"
fi

# Create Cloud NAT if not exists
if ! gcloud compute routers nats describe $NAT_NAME --router=$ROUTER_NAME --router-region=$REGION --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "🌍 Creating Cloud NAT $NAT_NAME..."
    gcloud compute routers nats create $NAT_NAME \
        --router=$ROUTER_NAME \
        --router-region=$REGION \
        --nat-all-subnet-ip-ranges \
        --auto-allocate-nat-external-ips \
        --project=$PROJECT_ID
else
    echo "✅ Cloud NAT $NAT_NAME already exists"
fi

# Get cluster credentials
echo "🔑 Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME \
    --zone=$ZONE \
    --project=$PROJECT_ID

# Verify cluster access
echo "🔍 Verifying cluster access..."
kubectl get nodes

# Install NGINX Ingress Controller
echo "🌐 Installing NGINX Ingress Controller..."
if ! kubectl get namespace ingress-nginx >/dev/null 2>&1; then
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
    
    echo "⏳ Waiting for NGINX Ingress Controller to be ready..."
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=300s
else
    echo "✅ NGINX Ingress Controller already installed"
fi

# Install cert-manager for SSL certificates
echo "🔒 Installing cert-manager..."
if ! kubectl get namespace cert-manager >/dev/null 2>&1; then
    kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    
    echo "⏳ Waiting for cert-manager to be ready..."
    kubectl wait --namespace cert-manager \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/instance=cert-manager \
        --timeout=300s
        
    # Create ClusterIssuer for Let's Encrypt
    cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@$PROJECT_ID.iam.gserviceaccount.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
else
    echo "✅ cert-manager already installed"
fi

# Create storage class for CMBCluster
echo "💾 Setting up storage classes..."
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: cmbcluster-ssd
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  replication-type: none
allowVolumeExpansion: true
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
EOF

echo "✅ Private CMBCluster infrastructure setup complete!"
echo ""
echo "📋 Summary:"
echo "- Network: $NETWORK_NAME"
echo "- Subnet: $SUBNET_NAME"
echo "- Cluster: $CLUSTER_NAME"
echo "- Authorized IP: $MY_IP/32"
echo "- Master CIDR: 172.16.0.0/28"
echo "- Pods CIDR: 10.1.0.0/16"
echo "- Services CIDR: 10.2.0.0/20"
echo ""
echo "📝 Next steps:"
echo "1. Configure your domain DNS to point to the ingress IP"
echo "2. Set up OAuth credentials in Google Cloud Console"
echo "3. Run: ./scripts/deploy.sh $PROJECT_ID your-domain.com"
echo ""
echo "🔍 Useful commands:"
echo "kubectl get nodes"
echo "kubectl get service -n ingress-nginx"
echo "gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE"
