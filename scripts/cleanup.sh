#!/bin/bash
set -e

# Configuration - should match setup-cluster.sh for consistency
PROJECT_ID=${1:-$(gcloud config get-value project)}
CLUSTER_NAME=${2:-"cmbcluster"}
REGION=${3:-"us-central1"}
ZONE=${4:-"us-central1-a"}
CONFIRM=${5:-"no"}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is required"
    echo "Usage: $0 <PROJECT_ID> [CLUSTER_NAME] [REGION] [ZONE] [yes]"
    exit 1
fi

ARTIFACT_REGISTRY_NAME="${CLUSTER_NAME}-images"
# Define resource names based on conventions in setup-cluster.sh and deploy.sh
NETWORK_NAME="${CLUSTER_NAME}-network"
SUBNET_NAME="${CLUSTER_NAME}-subnet"
ROUTER_NAME="${CLUSTER_NAME}-nat-router"
NAT_NAME="${CLUSTER_NAME}-nat-config"
WORKLOAD_SA_NAME="${CLUSTER_NAME}-workload-sa"
WORKLOAD_SA_EMAIL="${WORKLOAD_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
HELM_RELEASE_NAME="cmbcluster" # As per deploy.sh
K8S_NAMESPACE="cmbcluster"     # As per deploy.sh

if [ "$CONFIRM" != "yes" ]; then
    echo "⚠️ This will delete ALL CMBCluster resources!"
    echo "This includes:"
    echo "- All user environments and data"
    echo "- The GKE cluster ($CLUSTER_NAME) and its node pools"
    echo "- All persistent volumes"
    echo "- All container images"
    echo "- Cloud NAT, Router, VPC Network, and Subnet"
    echo "- Firewall rules"
    echo "- IAM Service Account"
    echo ""
    read -p "Are you sure? Type 'yes' to continue: " CONFIRM
fi

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

echo "🧹 Cleaning up CMBCluster resources for project $PROJECT_ID..."

# Set the default project to ensure commands run against the correct one
gcloud config set project $PROJECT_ID

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

# Note: Persistent Volumes with reclaimPolicy:Delete are removed when the namespace is deleted.

# Delete GKE cluster
if gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "🗑️ Deleting GKE cluster '$CLUSTER_NAME' (this may take a few minutes)..."
    gcloud container clusters delete $CLUSTER_NAME --zone=$ZONE --project=$PROJECT_ID --quiet
else
    echo "✅ GKE cluster '$CLUSTER_NAME' not found, skipping."
fi

# Delete Cloud NAT (must be deleted before the router)
if gcloud compute routers nats describe $NAT_NAME --router=$ROUTER_NAME --router-region=$REGION --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "🗑️ Deleting Cloud NAT '$NAT_NAME'..."
    gcloud compute routers nats delete $NAT_NAME --router=$ROUTER_NAME --router-region=$REGION --project=$PROJECT_ID --quiet
else
    echo "✅ Cloud NAT '$NAT_NAME' not found, skipping."
fi

# Delete Cloud Router
if gcloud compute routers describe $ROUTER_NAME --region=$REGION --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "🗑️ Deleting Cloud Router '$ROUTER_NAME'..."
    gcloud compute routers delete $ROUTER_NAME --region=$REGION --project=$PROJECT_ID --quiet
else
    echo "✅ Cloud Router '$ROUTER_NAME' not found, skipping."
fi

# Delete Firewall Rules
for rule in ${CLUSTER_NAME}-allow-internal ${CLUSTER_NAME}-allow-health-checks ${CLUSTER_NAME}-allow-master; do
    if gcloud compute firewall-rules describe $rule --project=$PROJECT_ID >/dev/null 2>&1; then
        echo "🗑️ Deleting firewall rule '$rule'..."
        gcloud compute firewall-rules delete $rule --project=$PROJECT_ID --quiet
    else
        echo "✅ Firewall rule '$rule' not found, skipping."
    fi
done

# Delete Subnet (must be deleted before the VPC network)
if gcloud compute networks subnets describe $SUBNET_NAME --region=$REGION --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "🗑️ Deleting subnet '$SUBNET_NAME'..."
    gcloud compute networks subnets delete $SUBNET_NAME --region=$REGION --project=$PROJECT_ID --quiet
else
    echo "✅ Subnet '$SUBNET_NAME' not found, skipping."
fi

# Delete VPC Network
if gcloud compute networks describe $NETWORK_NAME --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "🗑️ Deleting VPC network '$NETWORK_NAME'..."
    gcloud compute networks delete $NETWORK_NAME --project=$PROJECT_ID --quiet
else
    echo "✅ VPC network '$NETWORK_NAME' not found, skipping."
fi

# Delete IAM Service Account
if gcloud iam service-accounts describe $WORKLOAD_SA_EMAIL --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "🗑️ Deleting IAM Service Account '$WORKLOAD_SA_EMAIL'..."
    gcloud iam service-accounts delete $WORKLOAD_SA_EMAIL --project=$PROJECT_ID --quiet
else
    echo "✅ IAM Service Account '$WORKLOAD_SA_EMAIL' not found, skipping."
fi

# Delete container image packages from Artifact Registry
echo "🗑️ Deleting container images from Artifact Registry..."
for image in cmbcluster-backend cmbcluster-frontend cmbcluster-user-env; do
    if gcloud artifacts packages describe $image --repository=$ARTIFACT_REGISTRY_NAME --location=$REGION --project=$PROJECT_ID >/dev/null 2>&1; then
        echo "   - Deleting package '$image' from repository '$ARTIFACT_REGISTRY_NAME'..."
        gcloud artifacts packages delete $image --repository=$ARTIFACT_REGISTRY_NAME --location=$REGION --project=$PROJECT_ID --quiet --async
    else
        echo "✅ Image package '$image' not found in Artifact Registry, skipping."
    fi
done

echo "✅ Cleanup complete! Some resources like DNS records and OAuth credentials must be removed manually."
