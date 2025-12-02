# Deployment Guide

Complete production deployment instructions for GCP. AWS integration coming in Q2-Q4 2025.

## Prerequisites

### Required Software
- `kubectl` (1.24+)
- `helm` (3.10+)
- `gcloud` CLI (for GCP)
- `docker` and `docker-compose`
- Git

### Required Accounts
- GCP account with billing enabled
- Domain name with DNS access
- Google Container Registry (GCR) for Docker images

### Knowledge Requirements
- Basic Kubernetes concepts
- Understanding of GCP console
- DNS configuration experience

---

## Quick Start (GCP)

```bash
# 1. Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Setup infrastructure (creates cluster)
./scripts/setup-cluster.sh YOUR_PROJECT_ID us-central1

# 3. Configure Google OAuth (see section below)

# 4. Build images
./scripts/build-images.sh YOUR_PROJECT_ID

# 5. Deploy
./scripts/deploy.sh YOUR_PROJECT_ID your-domain.com

# 6. Configure DNS
# Point your domain to the ingress IP returned by deploy script
```

---

## Step-by-Step Deployment

### 1. Create Cloud Infrastructure

#### Google Cloud Platform (GKE)

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Create GKE cluster with autoscaling
gcloud container clusters create cmbcluster \
  --region us-central1 \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10 \
  --enable-autorepair \
  --enable-autoupgrade \
  --addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver \
  --workload-pool=YOUR_PROJECT_ID.svc.id.goog

# Get cluster credentials
gcloud container clusters get-credentials cmbcluster --region us-central1

# Verify connection
kubectl cluster-info
kubectl get nodes
```

#### AWS (EKS) - Coming in Q2-Q4 2025

AWS EKS integration is in development with planned features:
- Terraform templates for automated cluster creation
- ECR (Elastic Container Registry) support
- AWS Load Balancer integration
- Cost optimization guidelines
- Track progress: [GitHub Issues](https://github.com/CMBAgents/cmbcluster/issues)

```bash
# AWS support coming soon
# Check back in Q2-Q4 2025
```

#### Azure (AKS) - Not Currently Planned

Azure AKS is not currently in the roadmap. If you need Azure support:
1. Open a feature request on [GitHub Issues](https://github.com/CMBAgents/cmbcluster/issues)
2. Community contributions are welcome!

### 2. Install Required Add-ons

#### NGINX Ingress Controller

```bash
# Add Helm repository
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install ingress controller
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer \
  --set controller.metrics.enabled=true

# Verify
kubectl get svc -n ingress-nginx
# Note the EXTERNAL-IP
```

#### cert-manager (TLS Certificates)

```bash
# Add Helm repository
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Install cert-manager
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true \
  --set global.leaderElection.namespace=cert-manager

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@your-domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Verify
kubectl get clusterissuer
```

### 3. Setup Container Registry

#### Google Container Registry (GCR)

```bash
# Configure Docker authentication
gcloud auth configure-docker gcr.io

# Tag images
docker tag cmbcluster-backend gcr.io/YOUR_PROJECT_ID/cmbcluster-backend:latest
docker tag cmbcluster-frontend gcr.io/YOUR_PROJECT_ID/cmbcluster-frontend:latest

# Push images
docker push gcr.io/YOUR_PROJECT_ID/cmbcluster-backend:latest
docker push gcr.io/YOUR_PROJECT_ID/cmbcluster-frontend:latest
```

#### AWS Elastic Container Registry (ECR) - Coming in Q2-Q4 2025

```bash
# AWS ECR support coming soon with full integration
# Check back in Q2-Q4 2025
```

#### Docker Hub (Alternative)

```bash
# Tag images
docker tag cmbcluster-backend YOUR_USERNAME/cmbcluster-backend:latest
docker tag cmbcluster-frontend YOUR_USERNAME/cmbcluster-frontend:latest

# Push images
docker push YOUR_USERNAME/cmbcluster-backend:latest
docker push YOUR_USERNAME/cmbcluster-frontend:latest
```

### 4. Configure Google OAuth 2.0

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services > Credentials**
3. Click **Create Credentials > OAuth 2.0 Client ID**
4. Select **Web application**
5. Add authorized redirect URIs:
   ```
   https://your-domain.com/auth/callback
   https://api.your-domain.com/auth/callback
   https://localhost:8000/auth/callback  (for testing)
   ```
6. Click **Create**
7. Copy Client ID and Client Secret

### 5. Create Kubernetes Secrets

```bash
# Create namespace
kubectl create namespace cmbcluster

# Create OAuth secret
kubectl create secret generic oauth-credentials \
  --from-literal=google_client_id=YOUR_CLIENT_ID \
  --from-literal=google_client_secret=YOUR_CLIENT_SECRET \
  -n cmbcluster

# Create secret key for JWT
SECRET_KEY=$(openssl rand -base64 32)
kubectl create secret generic app-secrets \
  --from-literal=secret_key=$SECRET_KEY \
  -n cmbcluster

# Verify
kubectl get secrets -n cmbcluster
```

### 6. Configure Helm Values

Edit `helm/values.yaml`:

```yaml
# Image registry (change based on cloud provider)
image:
  registry: gcr.io/YOUR_PROJECT_ID  # or ECR/Docker Hub

# Domain configuration
domain: your-domain.com
baseUrl: https://your-domain.com
apiUrl: https://api.your-domain.com

# Replica counts
backend:
  replicaCount: 2
frontend:
  replicaCount: 2

# Resource limits
backend:
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1Gi

# Auto-scaling
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

# Storage
storage:
  size: 10Gi
  storageClass: standard  # GKE: standard, EKS: gp2, AKS: default

# Environment variables
env:
  DEV_MODE: "false"
  DEBUG: "false"
  TOKEN_EXPIRE_HOURS: "8"
  FREE_TIER_MAX_UPTIME_MINUTES: "60"
```

### 7. Deploy with Helm

```bash
# Add Helm repository (if using official chart)
helm repo add cmbcluster https://charts.cmbcluster.io
helm repo update

# Or deploy from local directory
helm install cmbcluster ./helm \
  --namespace cmbcluster \
  --create-namespace \
  -f helm/values.yaml

# Verify deployment
kubectl get pods -n cmbcluster
kubectl get svc -n cmbcluster
kubectl get ingress -n cmbcluster

# Wait for pods to be ready
kubectl wait --for=condition=ready pod \
  -l app=cmbcluster-backend \
  -n cmbcluster \
  --timeout=300s
```

### 8. Configure DNS

```bash
# Get ingress external IP
INGRESS_IP=$(kubectl get ingress -n cmbcluster \
  -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}')

echo "Ingress IP: $INGRESS_IP"

# Create DNS records:
# A record: your-domain.com -> $INGRESS_IP
# A record: api.your-domain.com -> $INGRESS_IP
# CNAME: www.your-domain.com -> your-domain.com (optional)
```

DNS propagation takes 5-30 minutes. Test with:
```bash
nslookup your-domain.com
nslookup api.your-domain.com
```

### 9. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n cmbcluster

# Check services
kubectl get svc -n cmbcluster

# Check ingress
kubectl get ingress -n cmbcluster

# Check certificates
kubectl get certificates -n cmbcluster

# Check backend health
curl https://api.your-domain.com/health

# Check frontend
curl https://your-domain.com/

# View logs
kubectl logs -f deployment/cmbcluster-backend -n cmbcluster
kubectl logs -f deployment/cmbcluster-frontend -n cmbcluster
```

---

## Configuration

### Environment Variables

Create a `.env` file before deploying:

```bash
# Required
PROJECT_ID=your-project-id
BASE_DOMAIN=your-domain.com
GOOGLE_CLIENT_ID=your-oauth-client-id
GOOGLE_CLIENT_SECRET=your-oauth-client-secret
SECRET_KEY=$(openssl rand -base64 32)

# Optional but recommended
API_URL=https://api.your-domain.com
FRONTEND_URL=https://your-domain.com
DEV_MODE=false
DEBUG=false
TOKEN_EXPIRE_HOURS=8
FREE_TIER_MAX_UPTIME_MINUTES=60
ADMIN_EMAILS=admin@your-domain.com
```

### Kubernetes ConfigMap

```bash
# Create from env file
kubectl create configmap app-config \
  --from-env-file=.env \
  -n cmbcluster
```

### Helm Custom Values

```yaml
# helm/custom-values.yaml
global:
  environment: production
  
backend:
  env:
    - name: PROJECT_ID
      value: "your-project-id"
    - name: BASE_DOMAIN
      value: "your-domain.com"
    - name: DEV_MODE
      value: "false"

ingress:
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: your-domain.com
      paths:
        - path: /
          pathType: Prefix
    - host: api.your-domain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: cmbcluster-tls
      hosts:
        - your-domain.com
        - api.your-domain.com
```

---

## Scaling Configuration

### Horizontal Scaling (More Replicas)

```bash
# Scale backend to 5 replicas
kubectl scale deployment cmbcluster-backend \
  --replicas=5 \
  -n cmbcluster

# Scale frontend to 3 replicas
kubectl scale deployment cmbcluster-frontend \
  --replicas=3 \
  -n cmbcluster

# Enable auto-scaling
kubectl autoscale deployment cmbcluster-backend \
  --min=2 \
  --max=10 \
  --cpu-percent=70 \
  -n cmbcluster
```

### Vertical Scaling (More Resources)

```yaml
# helm/values.yaml
backend:
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2000m
      memory: 2Gi
```

### Node Scaling

```bash
# GKE
gcloud container clusters update cmbcluster \
  --enable-autoscaling \
  --min-nodes=2 \
  --max-nodes=20 \
  --region us-central1

# EKS
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name eks-workers \
  --desired-capacity 5

# AKS
az aks nodepool update \
  --resource-group cmbcluster-rg \
  --cluster-name cmbcluster \
  --name nodepool1 \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 20
```

---

## Upgrades & Maintenance

### Update Helm Chart

```bash
# Pull latest chart
helm repo update

# Upgrade deployment
helm upgrade cmbcluster ./helm \
  --namespace cmbcluster \
  -f helm/values.yaml

# Verify upgrade
kubectl rollout status deployment/cmbcluster-backend -n cmbcluster
kubectl rollout status deployment/cmbcluster-frontend -n cmbcluster
```

### Backup Database

```bash
# Export database
kubectl exec -it deployment/cmbcluster-backend -n cmbcluster -- \
  pg_dump -U postgres cmbcluster > backup.sql

# Or for SQLite
kubectl cp cmbcluster/cmbcluster-backend:/app/data/cmbcluster.db \
  ./cmbcluster.db.backup
```

### Restore from Backup

```bash
# For PostgreSQL
kubectl exec -it deployment/cmbcluster-backend -n cmbcluster -- \
  psql -U postgres cmbcluster < backup.sql
```

---

## Monitoring & Logging

### Enable Prometheus Monitoring

```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

### View Logs

```bash
# Real-time backend logs
kubectl logs -f deployment/cmbcluster-backend -n cmbcluster

# Real-time frontend logs
kubectl logs -f deployment/cmbcluster-frontend -n cmbcluster

# Logs from specific pod
kubectl logs -f POD_NAME -n cmbcluster

# Last 50 lines
kubectl logs deployment/cmbcluster-backend -n cmbcluster --tail=50
```

### Port Forwarding (Local Access)

```bash
# Access backend on localhost:8000
kubectl port-forward service/cmbcluster-backend 8000:8000 -n cmbcluster

# Access frontend on localhost:3000
kubectl port-forward service/cmbcluster-frontend 3000:3000 -n cmbcluster
```

---

## Troubleshooting Deployments

### Ingress Not Getting IP

```bash
# Check ingress status
kubectl describe ingress cmbcluster-ingress -n cmbcluster

# Wait for IP assignment (can take 2-5 minutes)
kubectl get ingress -n cmbcluster -w
```

### Pods Stuck in Pending

```bash
# Check why pod isn't scheduled
kubectl describe pod POD_NAME -n cmbcluster

# Check node resources
kubectl top nodes
kubectl describe node NODE_NAME
```

### Certificate Issues

```bash
# Check certificate status
kubectl describe certificate cmbcluster-tls -n cmbcluster

# View certificate details
kubectl get secret cmbcluster-tls -n cmbcluster -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -text -noout
```

---

## Roadmap

### Q1 2025
- [x] Core infrastructure
- [x] Basic monitoring
- [ ] Enhanced alerting

### Q2-Q4 2025
- [ ] Multi-region deployment
- [ ] Disaster recovery automation
- [ ] Advanced cost optimization
- [ ] Multi-cloud federation
