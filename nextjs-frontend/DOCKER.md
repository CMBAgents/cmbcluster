# Next.js Frontend - Docker & Production Setup

This document describes the Docker configuration and production deployment setup for the Next.js frontend that replaces the Streamlit frontend while maintaining exact API compatibility and running on port 8501.

## Architecture Overview

The Next.js frontend is designed to be a drop-in replacement for the Streamlit frontend:

- **Port**: 8501 (same as Streamlit)
- **Health Check**: `/api/health` (replaces `/_stcore/health`)
- **Authentication**: NextAuth.js with Google OAuth
- **API Integration**: Identical endpoints as Streamlit version
- **Docker**: Multi-stage build optimized for production

## Production Configuration

### Environment Variables

Configure these variables in your `.env` file at the project root:

```bash
# Frontend-specific variables (will be passed to Next.js container)
NEXTAUTH_SECRET=your-production-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# API Configuration
API_URL=https://api.your-domain.com
BASE_DOMAIN=your-domain.com

# Deployment settings
PROJECT_ID=your-gcp-project-id
DOMAIN=your-domain.com
CLUSTER_NAME=cmbcluster
REGION=us-central1
TAG=latest
```

## Docker Configuration

### Multi-Stage Dockerfile

The Dockerfile follows a 4-stage build process:

1. **Base**: Node.js 18-alpine with system dependencies
2. **Dependencies**: Install and cache production dependencies
3. **Builder**: Build the Next.js application
4. **Runner**: Final production image with minimal footprint

### Key Features

- **Security**: Non-root user (UID 1001, matching Python container)
- **Health Checks**: Same pattern as Python container (30s interval)
- **Port**: 8501 (exact replacement for Streamlit)
- **Optimization**: Standalone Next.js build for minimal container size

## Deployment Process

### 1. Configure Environment

Edit `.env` file in project root with your production values:

```bash
# Copy from existing .env or create new
cp .env.example .env
# Edit with your values
vi .env
```

### 2. Build and Deploy

Use the existing deployment infrastructure:

```bash
# Build all images including Next.js frontend
bash scripts/deploy.sh

# Or with specific parameters
bash scripts/deploy.sh PROJECT_ID CLUSTER_NAME DOMAIN REGION ZONE TAG
```

### 3. Verify Deployment

Check that all services are running:

```bash
kubectl get pods -n cmbcluster
kubectl logs -f deployment/cmbcluster-frontend -n cmbcluster
```

Access the application:
- Frontend: https://your-domain.com
- API: https://api.your-domain.com
- Health: https://your-domain.com/api/health

## Integration with Existing Infrastructure

### Helm Configuration

The frontend is deployed using the existing Helm chart with updated values:

- **Image**: Built from `nextjs-frontend/` directory
- **Port**: 8501 (no change required)
- **Health Check**: Updated to `/api/health`
- **Environment**: Production-optimized settings

### Build Process Integration

Updated `scripts/build-images.sh` to include Next.js:

```bash
# Builds backend, frontend (Next.js), and user-environment
SERVICES=("frontend" "backend" "user-environment")
```

The script automatically uses `nextjs-frontend/` directory for the frontend service.

## Production Optimizations

### Next.js Configuration

- **Standalone Output**: Enabled for Docker optimization
- **Bundle Analysis**: Available with `ANALYZE=true`
- **Image Optimization**: Configured for production domains
- **Compression**: Enabled for better performance
- **Telemetry**: Disabled for privacy

### Security Features

- **Non-root User**: Runs as `nextjs` user (UID 1001)
- **Read-only Filesystem**: Enhanced container security
- **Minimal Attack Surface**: Multi-stage build removes unnecessary files
- **HTTPS Only**: Production environment enforces secure connections

## Monitoring & Maintenance

### Health Monitoring

Health endpoint provides comprehensive status:
```bash
curl -f https://your-domain.com/api/health
```

### Log Analysis

View application logs:
```bash
kubectl logs -f deployment/cmbcluster-frontend -n cmbcluster
```

### Performance Monitoring

Built-in monitoring for:
- Response times
- Memory usage
- Error rates
- User authentication flow

## Troubleshooting

### Common Issues

1. **Build Failures**: Check Node.js version and dependencies
2. **Health Check Failures**: Verify `/api/health` endpoint
3. **Authentication Issues**: Confirm Google OAuth configuration
4. **API Connection**: Check backend service connectivity

### Debug Commands

```bash
# Check container status
kubectl describe pod -l app.kubernetes.io/component=frontend -n cmbcluster

# View detailed logs
kubectl logs -f deployment/cmbcluster-frontend -n cmbcluster --tail=100

# Test API connectivity
kubectl exec -it deployment/cmbcluster-frontend -n cmbcluster -- curl -f http://localhost:8501/api/health
```

## Rollback Procedure

If needed, rollback to Streamlit frontend:

1. Update Helm values to use Streamlit image
2. Redeploy using existing process
3. Update health check endpoint to `/_stcore/health`

The API endpoints and functionality remain identical, ensuring seamless transitions.

## Performance Expectations

### Resource Usage
- **Memory**: ~200MB (vs ~300MB Streamlit)
- **CPU**: ~0.1 cores baseline
- **Startup Time**: ~10-15 seconds
- **Cold Start**: ~5 seconds

### Scaling
- **Horizontal**: Supports multiple replicas
- **Load Balancing**: Works with existing ingress
- **Session Handling**: Stateless design for scalability
