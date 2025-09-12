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
PROJECT_ID=${1:-$PROJECT_ID}
CLUSTER_NAME=${2:-$CLUSTER_NAME}
REGION=${3:-$REGION}
ZONE=${4:-$ZONE}
RELEASE_CHANNEL=${5:-$RELEASE_CHANNEL}

# Set final defaults if variables are still not set
PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project)}
CLUSTER_NAME=${CLUSTER_NAME:-"cmbcluster"}
REGION=${REGION:-"us-central1"}
ZONE=${ZONE:-"${ZONE}"}
RELEASE_CHANNEL=${RELEASE_CHANNEL:-"regular"} # Options: rapid, regular, stable

# Validate required variables
if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is required. Set it in .env or pass as an argument."
    echo "Usage: $0 [PROJECT_ID] [CLUSTER_NAME] [REGION] [ZONE] [RELEASE_CHANNEL]"
    exit 1
fi

echo "🚀 Setting up CMBCluster private GKE infrastructure..."
echo "--------------------------------------------------"
echo "Project:      $PROJECT_ID"
echo "Cluster:      $CLUSTER_NAME"
echo "Region:       $REGION"
echo "Zone:         $ZONE"
echo "Channel:      $RELEASE_CHANNEL"
echo "--------------------------------------------------"

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
gcloud services enable artifactregistry.googleapis.com

# Create VPC network if not exists
if ! gcloud compute networks describe $NETWORK_NAME --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "🌐 Creating VPC network $NETWORK_NAME..."
    gcloud compute networks create $NETWORK_NAME \
        --subnet-mode=custom \
        --project=$PROJECT_ID
else
    echo "✅ VPC network $NETWORK_NAME already exists"
fi

# Create Artifact Registry repository if not exists
ARTIFACT_REGISTRY_NAME="${CLUSTER_NAME}-images"
if ! gcloud artifacts repositories describe $ARTIFACT_REGISTRY_NAME --location=$REGION --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "📦 Creating Artifact Registry repository '$ARTIFACT_REGISTRY_NAME'..."
    gcloud artifacts repositories create $ARTIFACT_REGISTRY_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="Docker images for CMBCluster" \
        --project=$PROJECT_ID
else
    echo "✅ Artifact Registry repository '$ARTIFACT_REGISTRY_NAME' already exists"
fi

# Create Cloud Storage bucket for SQLite database storage
BUCKET_NAME="${PROJECT_ID}-${CLUSTER_NAME}-db"
if ! gsutil ls -b gs://$BUCKET_NAME >/dev/null 2>&1; then
    echo "🪣 Creating Cloud Storage bucket '$BUCKET_NAME' for database storage..."
    gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME
    
    # Enable versioning for backup/recovery
    gsutil versioning set on gs://$BUCKET_NAME
    
    # Set lifecycle policy to manage versions (keep last 30 versions)
    cat > /tmp/lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "numNewerVersions": 30
        }
      }
    ]
  }
}
EOF
    gsutil lifecycle set /tmp/lifecycle.json gs://$BUCKET_NAME
    rm /tmp/lifecycle.json
    
    echo "✅ Cloud Storage bucket '$BUCKET_NAME' created with versioning enabled"
else
    echo "✅ Cloud Storage bucket '$BUCKET_NAME' already exists"
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
if ! gcloud compute firewall-rules describe ${CLUSTER_NAME}-allow-internal --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "Creating firewall rule ${CLUSTER_NAME}-allow-internal..."
    gcloud compute firewall-rules create ${CLUSTER_NAME}-allow-internal \
        --network=$NETWORK_NAME \
        --allow=tcp,udp,icmp \
        --source-ranges=10.0.0.0/8 \
        --project=$PROJECT_ID \
        --quiet
else
    echo "✅ Firewall rule ${CLUSTER_NAME}-allow-internal already exists"
fi

# Allow Google health checks
if ! gcloud compute firewall-rules describe ${CLUSTER_NAME}-allow-health-checks --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "Creating firewall rule ${CLUSTER_NAME}-allow-health-checks..."
    gcloud compute firewall-rules create ${CLUSTER_NAME}-allow-health-checks \
        --network=$NETWORK_NAME \
        --allow=tcp \
        --source-ranges=130.211.0.0/22,35.191.0.0/16 \
        --target-tags=gke-node \
        --project=$PROJECT_ID \
        --quiet
else
    echo "✅ Firewall rule ${CLUSTER_NAME}-allow-health-checks already exists"
fi

# Allow master to communicate with nodes (CRITICAL for webhooks and probes in private clusters)
if ! gcloud compute firewall-rules describe ${CLUSTER_NAME}-allow-master --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "Creating firewall rule to allow master communication to nodes..."
    gcloud compute firewall-rules create ${CLUSTER_NAME}-allow-master \
        --network=$NETWORK_NAME \
        --allow=tcp,udp,icmp \
        --source-ranges=172.16.0.0/28 \
        --project=$PROJECT_ID \
        --quiet
else
    echo "✅ Firewall rule for master communication already exists"
fi

# Create private GKE cluster
echo "🏗️ Creating private GKE cluster..."
if ! gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE --project=$PROJECT_ID >/dev/null 2>&1; then
    # Using e2-standard-2 for better cost/performance than n1-standard-2
    # Using pd-balanced for node disk type for better performance than pd-standard
    # Note: The 'cmbcluster-ssd' StorageClass is for PVCs, not node boot disks.
    gcloud container clusters create $CLUSTER_NAME \
        --release-channel=$RELEASE_CHANNEL \
        --zone=$ZONE \
        --network=$NETWORK_NAME \
        --subnetwork=$SUBNET_NAME \
        --cluster-ipv4-cidr=10.1.0.0/16 \
        --services-ipv4-cidr=10.2.0.0/20 \
        --enable-ip-alias \
        --enable-private-nodes \
        --master-ipv4-cidr=172.16.0.0/28 \
        --enable-master-authorized-networks \
        --master-authorized-networks=$MY_IP/32 \
        --default-max-pods-per-node=110 \
        --node-locations=$ZONE \
        --num-nodes=1 \
        --min-nodes=1 \
        --max-nodes=3 \
        --machine-type=e2-standard-2 \
        --disk-type=pd-balanced \
        --disk-size=50GB \
        --image-type=COS_CONTAINERD \
        --metadata=disable-legacy-endpoints=true \
        --addons=GcsFuseCsiDriver \
        --project=$PROJECT_ID

    echo "⏳ Waiting for cluster $CLUSTER_NAME to be ready..."
    gcloud container clusters wait $CLUSTER_NAME \
        --zone=$ZONE \
        --project=$PROJECT_ID \
        --ready
else
    echo "✅ Cluster $CLUSTER_NAME already exists"
    
    # Enable Cloud Storage FUSE CSI driver on existing cluster if not already enabled
    echo "🔧 Ensuring Cloud Storage FUSE CSI driver is enabled..."
    gcloud container clusters update $CLUSTER_NAME \
        --zone=$ZONE \
        --update-addons=GcsFuseCsiDriver=ENABLED \
        --project=$PROJECT_ID \
        --quiet || echo "ℹ️ CSI driver already enabled or update not needed"
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
    privateKeySecretRef: # This secret will be created by cert-manager
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
else
    echo "✅ cert-manager already installed"
fi

# Set up Workload Identity Service Account
echo "🔑 Setting up Workload Identity Service Account..."
WORKLOAD_SA_NAME="${CLUSTER_NAME}-workload-sa"
WORKLOAD_SA_EMAIL="${WORKLOAD_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe $WORKLOAD_SA_EMAIL --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "Creating Google Service Account: $WORKLOAD_SA_EMAIL..."
    gcloud iam service-accounts create $WORKLOAD_SA_NAME \
        --display-name="CMBCluster Workload Identity SA" \
        --project=$PROJECT_ID
else
    echo "✅ Google Service Account $WORKLOAD_SA_EMAIL already exists"
fi

# Grant Storage Object Viewer role for image pulling
echo "Granting roles/storage.objectViewer to $WORKLOAD_SA_EMAIL..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$WORKLOAD_SA_EMAIL" \
    --role="roles/storage.objectViewer" \
    --quiet || echo "✅ roles/storage.objectViewer already granted to $WORKLOAD_SA_EMAIL"

# Grant Storage Object Admin role for database bucket access
echo "Granting roles/storage.objectAdmin to $WORKLOAD_SA_EMAIL for database bucket..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$WORKLOAD_SA_EMAIL" \
    --role="roles/storage.objectAdmin" \
    --quiet || echo "✅ roles/storage.objectAdmin already granted to $WORKLOAD_SA_EMAIL"

# Grant bucket access specifically for the database bucket
echo "Granting bucket-specific permissions for $BUCKET_NAME..."
gsutil iam ch serviceAccount:$WORKLOAD_SA_EMAIL:objectAdmin gs://$BUCKET_NAME

# Grant broader GCS permissions for user bucket management
echo "🗂️ Configuring service account permissions for user bucket management..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$WORKLOAD_SA_EMAIL" \
    --role="roles/storage.admin" \
    --quiet || echo "ℹ️ Storage admin role already assigned"

# Set up bucket naming prefix for user buckets
USER_BUCKET_PREFIX="${PROJECT_ID}-${CLUSTER_NAME}-user"
echo "ℹ️ User buckets will use prefix: ${USER_BUCKET_PREFIX}-*"

# Note: The Kubernetes Service Account (KSA) and the IAM policy binding between KSA and GSA
# will be handled during deployment (e.g., in Helm chart or deploy.sh).

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
echo "- Pods CIDR: 10.1.0.0/16 (via secondary range)"
echo "- Services CIDR: 10.2.0.0/20 (via secondary range)"
echo "- Workload Identity SA: $WORKLOAD_SA_EMAIL"
echo ""
echo "📝 Next steps:"
echo "1. Configure your domain DNS to point to the ingress IP"
echo "2. Set up OAuth credentials in Google Cloud Console"
echo "3. Ensure your Helm chart or deployment manifests use the Kubernetes Service Account 'cmbcluster-ksa' (or similar) and annotate it with 'iam.gke.io/gcp-service-account=$WORKLOAD_SA_EMAIL'."
echo "4. Run: ./scripts/deploy.sh $PROJECT_ID your-domain.com"
echo ""
echo "🔍 Useful commands:"
echo "kubectl get nodes"
echo "kubectl get service -n ingress-nginx"
echo "gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE"
