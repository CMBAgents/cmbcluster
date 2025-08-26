#!/bin/bash
# Production Build Script for Next.js Frontend
# This script builds the Next.js application with production optimizations

set -e

echo "🚀 Building Next.js Frontend for Production"
echo "==========================================="

# Navigate to frontend directory
cd "$(dirname "$0")/../nextjs-frontend"

# Check if Node.js and npm are available
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is not installed"
    exit 1
fi

# Display versions
echo "📋 Environment Information:"
echo "Node.js: $(node --version)"
echo "npm: $(npm --version)"
echo "Current directory: $(pwd)"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf .next
rm -rf out
rm -rf node_modules/.cache

# Install dependencies
echo "📦 Installing dependencies..."
npm ci --only=production --prefer-offline --no-audit --progress=false

# Install development dependencies for build
echo "🔧 Installing build dependencies..."
npm ci --prefer-offline --no-audit --progress=false

# Type checking
echo "🔍 Type checking..."
npm run type-check || {
    echo "❌ Type checking failed"
    exit 1
}

# Run tests if available
if npm run --silent test --dry-run &> /dev/null; then
    echo "🧪 Running tests..."
    npm run test -- --passWithNoTests --watchAll=false
fi

# Build the application
echo "🏗️ Building Next.js application..."
export NODE_ENV=production
export NEXT_TELEMETRY_DISABLED=1

npm run build

# Verify build
if [ ! -d ".next" ]; then
    echo "❌ Build failed - .next directory not found"
    exit 1
fi

if [ ! -f ".next/standalone/server.js" ]; then
    echo "❌ Build failed - standalone server not generated"
    exit 1
fi

echo "✅ Build completed successfully!"
echo ""
echo "📊 Build Summary:"
du -sh .next 2>/dev/null || echo "Build size: Unknown"
echo "Standalone build: ✅"
echo "Static assets: ✅"
echo ""
echo "🐳 Ready for Docker build!"

# Optional: Run bundle analyzer if requested
if [ "$ANALYZE" = "true" ]; then
    echo "📈 Running bundle analysis..."
    ANALYZE=true npm run build
fi
