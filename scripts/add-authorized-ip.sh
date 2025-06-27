#!/bin/bash
set -e

# --- Configuration ---
# This script safely adds the current user's external IP to the GKE cluster's
# master authorized networks without removing existing entries.

PROJECT_ID=${1:-$(gcloud config get-value project)}
CLUSTER_NAME=${2:-"cmbcluster"}
ZONE=${3:-"us-central1-a"}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is required."
    echo "Usage: $0 [PROJECT_ID] [CLUSTER_NAME] [ZONE]"
    exit 1
fi

echo "🚀 Safely adding IP to master authorized networks for cluster '$CLUSTER_NAME'..."

# --- Logic ---
echo "🔍 Getting current external IP..."
CURRENT_IP=$(curl -s ifconfig.me)
if [ -z "$CURRENT_IP" ]; then
    echo "❌ Error: Could not determine external IP address."
    exit 1
fi
echo "  Your IP: $CURRENT_IP"
CURRENT_IP_CIDR="$CURRENT_IP/32"

echo "🔄 Fetching existing authorized networks..."
EXISTING_NETWORKS=$(gcloud container clusters describe $CLUSTER_NAME \
    --zone=$ZONE \
    --project=$PROJECT_ID \
    --format="value(masterAuthorizedNetworksConfig.cidrBlocks[].cidrBlock)" | tr ';' ',')

echo "  Existing networks: ${EXISTING_NETWORKS:-"None"}"

if [[ ",$EXISTING_NETWORKS," == *",$CURRENT_IP_CIDR,"* ]]; then
    echo "✅ Your IP ($CURRENT_IP_CIDR) is already in the authorized networks list. No changes needed."
    exit 0
fi

UPDATED_NETWORKS=${EXISTING_NETWORKS:+$EXISTING_NETWORKS,}$CURRENT_IP_CIDR
echo "  New list will be: $UPDATED_NETWORKS"

echo " GKE cluster..."
gcloud container clusters update $CLUSTER_NAME \
    --zone=$ZONE \
    --project=$PROJECT_ID \
    --enable-master-authorized-networks \
    --master-authorized-networks "$UPDATED_NETWORKS"

echo "✅ Successfully updated master authorized networks."