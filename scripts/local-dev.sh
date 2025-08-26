#!/bin/bash
set -e

echo "🚀 Starting CMBCluster local development environment..."

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is required but not installed"
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️ Please edit .env with your configuration before running again"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '#' | xargs)

# Create local development network
docker network create cmbcluster-network 2>/dev/null || true

# Start services
echo "🐳 Starting services with Docker Compose..."
docker-compose up --build --remove-orphans

echo "✅ Local development environment started!"
echo ""
echo "🌐 Access points:"
echo "Frontend: http://localhost:8501"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "User Environment: http://localhost:8502"
echo ""
echo "🛑 To stop: Ctrl+C or 'docker-compose down'"
