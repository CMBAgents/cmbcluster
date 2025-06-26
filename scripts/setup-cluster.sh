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

echo "🚀 Setting up CMBCluster infrastructure..."
echo "Project: $PROJECT_ID"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "Zone: $ZONE"

# Set the default project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📡 Enabling required APIs..."
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create GKE cluster
echo "🏗️ Creating GKE cluster..."
if ! gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE >/dev/null 2>&1; then
    gcloud container clusters create $CLUSTER_NAME \
        --zone=$ZONE \
        --num-nodes=3 \
        --node-locations=$ZONE \
        --machine-type=n1-standard-2 \
        --disk-size=50GB \
        --disk-type=pd-standard \
        --enable-autorepair \
        --enable-autoupgrade \
        --enable-autoscaling \
        --min-nodes=1 \
        --max-nodes=10 \
        --enable-network-policy \
        --enable-ip-alias \
        --workload-pool=$PROJECT_ID.svc.id.goog \
        --addons=HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver \
        --logging=SYSTEM,WORKLOAD \
        --monitoring=SYSTEM
else
    echo "✅ Cluster $CLUSTER_NAME already exists"
fi

# Get cluster credentials
echo "🔑 Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE

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

# Create storage class if needed
echo "💾 Setting up storage..."
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

# Deploy Terraform infrastructure if exists
if [ -d "terraform" ]; then
    echo "🏗️ Deploying Terraform infrastructure..."
    cd terraform
    terraform init
    terraform plan -var="project_id=$PROJECT_ID"
    terraform apply -var="project_id=$PROJECT_ID" -auto-approve
    cd ..
fi

echo "✅ Cluster setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Configure your domain DNS to point to the ingress IP"
echo "2. Set up OAuth credentials in Google Cloud Console"
echo "3. Run: ./scripts/deploy.sh $PROJECT_ID your-domain.com"
echo ""
echo "🔍 Get ingress IP:"
echo "kubectl get service ingress-nginx-controller -n ingress-nginx"
