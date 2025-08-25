#!/bin/bash

# Force redeploy script for authentication fixes
# This script ensures clean build and deployment

set -e

echo "🔄 Force redeploying with authentication fixes..."

# Check if we're in the right directory
if [ ! -f "./nextjs-frontend/package.json" ]; then
    echo "❌ Error: Please run this script from the repository root"
    exit 1
fi

# Clean any existing builds
echo "🧹 Cleaning previous builds..."
rm -rf ./nextjs-frontend/.next
rm -rf ./nextjs-frontend/out
docker system prune -f || true

# Rebuild NextJS frontend with cache busting
echo "🏗️ Building NextJS frontend with cache busting..."
cd nextjs-frontend
npm run build
cd ..

# Rebuild and push Docker images
echo "🐳 Rebuilding Docker images..."
./scripts/build-images.sh

# Redeploy to Kubernetes
echo "🚀 Redeploying to Kubernetes..."
./scripts/deploy.sh

echo "✅ Force redeploy completed!"
echo "🌐 Please hard refresh your browser (Ctrl+F5) to clear cache"
echo "🔍 Check logs with: kubectl logs -f deployment/cmbcluster-frontend -n cmbcluster"
