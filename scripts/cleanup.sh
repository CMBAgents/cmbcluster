#!/bin/bash
set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}
CONFIRM=${2:-"no"}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is required"
    echo "Usage: $0 <PROJECT_ID> [yes]"
    exit 1
fi

if [ "$CONFIRM" != "yes" ]; then
    echo "⚠️ This will delete ALL CMBCluster resources!"
    echo "This includes:"
    echo "- All user environments and data"
    echo "- The GKE cluster"
    echo "- All persistent volumes"
    echo "- All container images"
    echo ""
    read -p "Are you sure? Type 'yes' to continue: " CONFIRM
fi

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

echo "🧹 Cleaning up CMBCluster resources..."

# Delete Helm release
if helm list -n cmbcluster | grep -q cmbcluster; then
    echo "🗑️ Deleting Helm release..."
    helm uninstall cmbcluster -n cmbcluster
fi

# Delete namespace (this will delete all resources in it)
if kubectl get namespace cmbcluster >/dev/null 2>&1; then
    echo "🗑️ Deleting namespace..."
    kubectl delete namespace cmbcluster --wait=true
fi

# Delete persistent volumes
echo "🗑️ Deleting persistent volumes..."
kubectl get pv -o jsonpath='{.items[?(@.spec.claimRef.namespace=="cmbcluster")].metadata.name}' | \
    xargs -r kubectl delete pv

# Delete GKE cluster
if gcloud container clusters describe cmbcluster --zone=us-central1-b --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "🗑️ Deleting GKE cluster..."
    gcloud container clusters delete cmbcluster --zone=us-central1-b --project=$PROJECT_ID --quiet
fi

# Delete container images
echo "🗑️ Deleting container images..."
gcloud container images delete gcr.io/$PROJECT_ID/cmbcluster-backend --quiet || true
gcloud container images delete gcr.io/$PROJECT_ID/cmbcluster-frontend --quiet || true
gcloud container images delete gcr.io/$PROJECT_ID/cmbcluster-user-env --quiet || true

# Clean up Terraform state if exists
if [ -d "terraform" ] && [ -f "terraform/terraform.tfstate" ]; then
    echo "🗑️ Destroying Terraform resources..."
    cd terraform
    terraform destroy -var="project_id=$PROJECT_ID" -auto-approve
    cd ..
fi

echo "✅ Cleanup complete!"
echo ""
echo "📋 Remaining manual tasks:"
echo "1. Remove DNS records for $DOMAIN"
echo "2. Delete OAuth credentials in Google Cloud Console"
echo "3. Remove any remaining storage buckets"
