# CMBCluster - Polycloud Research Platform

**Multi-tenant Research Environment | Cloud-Agnostic | Enterprise-Ready**

CMBCluster is a multi-tenant research platform built on Kubernetes that runs on **Google Cloud Platform (GCP)** or **Amazon Web Services (AWS)** with a single codebase. Deploy anywhere, migrate anytime, with zero vendor lock-in.

[![Cloud Support](https://img.shields.io/badge/cloud-GCP%20%7C%20AWS-blue)](./docs/ARCHITECTURE_POLYCLOUD.md)
[![Auth Support](https://img.shields.io/badge/auth-Google%20OAuth%20%7C%20AWS%20Cognito-green)](./docs/ARCHITECTURE_POLYCLOUD.md#deployment-agnostic-authentication)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🌟 Key Features

### ☁️ **True Multi-Cloud Support**
- Deploy on **GCP (GKE)** or **AWS (EKS)** with the same codebase
- Switch cloud providers via configuration only
- No vendor lock-in, complete portability

### 🔐 **Deployment-Agnostic Authentication**
- Use **Google OAuth** on AWS or **AWS Cognito** on GCP
- Multi-provider support (both OAuth providers simultaneously)
- Enterprise-ready security (MFA, RBAC, role-based access)

### 🚀 **Enterprise-Grade Infrastructure**
- Kubernetes-native architecture
- Auto-scaling (horizontal pod autoscaling + cluster autoscaling)
- High availability with health checks
- TLS encryption with Let's Encrypt

### 🔬 **Research-Focused**
- Isolated user environments with persistent storage
- Pre-configured scientific computing stacks
- Collaborative tools and shared data access
- Interactive data analysis with Streamlit

---

## 🏗️ Architecture Overview

CMBCluster uses a **provider abstraction layer** to enable cloud-agnostic deployments:

```
┌──────────────────────────────────────────┐
│      Application Layer (Cloud-Agnostic)  │
│  FastAPI Backend + Next.js Frontend      │
└──────────────┬───────────────────────────┘
               │
┌──────────────▼───────────────────────────┐
│    Provider Abstraction Layer            │
│  Storage Provider │ Auth Provider        │
└──────┬─────────────┴───────┬─────────────┘
       │                     │
   ┌───▼────┐           ┌────▼────┐
   │  GCP   │           │   AWS   │
   │  GCS   │           │    S3   │
   │  GKE   │           │   EKS   │
   └────────┘           └─────────┘
```

**See [Architecture Documentation](./docs/ARCHITECTURE_POLYCLOUD.md) for detailed design.**

---

## 🚀 Quick Start

### Prerequisites

Choose your cloud provider:

<details>
<summary><b>For GCP Deployment</b></summary>

- **GCP Account** with billing enabled
- **Tools**:
  ```bash
  # Install gcloud, kubectl, helm
  curl https://sdk.cloud.google.com | bash
  gcloud components install kubectl
  curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
  ```
- **Domain** (or use nip.io for testing)
</details>

<details>
<summary><b>For AWS Deployment</b></summary>

- **AWS Account** with billing enabled
- **Tools**:
  ```bash
  # Install AWS CLI, kubectl, helm, eksctl
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  unzip awscliv2.zip && sudo ./aws/install

  curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
  sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

  curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
  ```
- **Domain** (or use load balancer DNS for testing)
</details>

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/cmbcluster.git
cd cmbcluster
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your cloud and auth settings
```

**Example configurations:**

<details>
<summary><b>GCP with Google OAuth (Default)</b></summary>

```bash
# .env
CLOUD_PROVIDER=gcp
PROJECT_ID=my-gcp-project
CLUSTER_NAME=cmbcluster
REGION=us-central1

AUTH_PROVIDER=auto
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=secret

DOMAIN=app.example.com
LETSENCRYPT_EMAIL=your-email@example.com
```
</details>

<details>
<summary><b>AWS with AWS Cognito (Default)</b></summary>

```bash
# .env
CLOUD_PROVIDER=aws
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1
EKS_CLUSTER_NAME=cmbcluster-eks

AUTH_PROVIDER=auto
COGNITO_USER_POOL_ID=us-east-1_XXXXX
COGNITO_CLIENT_ID=abc123
COGNITO_CLIENT_SECRET=secret
COGNITO_ISSUER=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXX

DOMAIN=app.example.com
LETSENCRYPT_EMAIL=your-email@example.com
```
</details>

<details>
<summary><b>AWS with Google OAuth (Deployment-Agnostic!)</b></summary>

```bash
# .env
CLOUD_PROVIDER=aws
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1
EKS_CLUSTER_NAME=cmbcluster-eks

AUTH_PROVIDER=google  # Use Google OAuth on AWS!
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=secret

DOMAIN=app.example.com
LETSENCRYPT_EMAIL=your-email@example.com
```
</details>

### 3. Deploy Infrastructure

<details>
<summary><b>Deploy on GCP</b></summary>

```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Setup cluster (15-25 minutes)
./scripts/gcp/setup-cluster.sh

# Build and push images (5-10 minutes)
./scripts/gcp/build-images.sh

# Deploy application (5-10 minutes)
./scripts/gcp/deploy.sh
```

**Total time:** ~30-40 minutes

**See [GCP Deployment Guide](./docs/DEPLOYMENT_GCP.md) for details.**
</details>

<details>
<summary><b>Deploy on AWS</b></summary>

```bash
# Authenticate with AWS
aws configure

# Setup cluster (20-30 minutes)
./scripts/aws/setup-cluster.sh

# (Optional) Setup Cognito for authentication
./scripts/aws/setup-cognito.sh

# Build and push images (5-10 minutes)
./scripts/aws/build-images.sh

# Deploy application (5-10 minutes)
./scripts/aws/deploy.sh
```

**Total time:** ~35-45 minutes

**See [AWS Deployment Guide](./docs/DEPLOYMENT_AWS.md) for details.**
</details>

### 4. Access Application

Visit `https://YOUR_DOMAIN` and sign in with your configured OAuth provider!

**First user becomes admin automatically.**

---

## 📖 Documentation

### Deployment Guides
- **[AWS Deployment Guide](./docs/DEPLOYMENT_AWS.md)** - Complete AWS deployment walkthrough
- **[GCP Deployment Guide](./docs/DEPLOYMENT_GCP.md)** - Complete GCP deployment walkthrough
- **[Polycloud Architecture](./docs/ARCHITECTURE_POLYCLOUD.md)** - Multi-cloud architecture details

### Operations
- **[Testing & Validation](./docs/TESTING.md)** - Comprehensive testing guide
- **[Configuration Reference](./.env.example)** - All environment variables explained

### Completion Reports
- [Phase 1: AWS Infrastructure](./PHASE1_COMPLETION.md)
- [Phase 2: Storage Abstraction](./PHASE2_COMPLETION.md)
- [Phase 3: Authentication](./PHASE3_COMPLETION.md)
- [Phase 4: Deployment](./PHASE4_COMPLETION.md)

---

## 🏛️ Architecture Components

### Application Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | FastAPI (Python) | REST API, authentication, pod orchestration |
| **Frontend** | Next.js (TypeScript) | Web UI, user dashboard |
| **Auth** | NextAuth.js | OAuth 2.0 integration |
| **Database** | SQLite on cloud storage | User data, environment metadata |

### Infrastructure (Cloud-Specific)

| Component | GCP | AWS |
|-----------|-----|-----|
| **Kubernetes** | GKE | EKS |
| **Object Storage** | Google Cloud Storage | Amazon S3 |
| **Storage Driver** | GCS FUSE CSI | S3 Mountpoint CSI |
| **Container Registry** | Artifact Registry | ECR |
| **IAM Binding** | Workload Identity | IRSA |
| **Load Balancer** | NGINX Ingress | AWS Load Balancer Controller |
| **Default Auth** | Google OAuth | AWS Cognito |

### Security Features

- ✅ **TLS Encryption**: Automatic Let's Encrypt certificates
- ✅ **OAuth 2.0**: Industry-standard authentication
- ✅ **RBAC**: Kubernetes role-based access control
- ✅ **Network Policies**: Pod-level network isolation
- ✅ **Security Headers**: CSP, HSTS, X-Frame-Options
- ✅ **Rate Limiting**: API protection
- ✅ **Secret Management**: Kubernetes secrets + cloud IAM

---

## 💻 Local Development

### Quick Start

```bash
# Start local environment
docker-compose up --build

# Access:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Development Scripts

```bash
# Validate configuration
./scripts/common/validate-config.sh

# Run tests
cd backend && pytest
cd nextjs-frontend && npm test

# Build images locally
docker build -t cmbcluster-backend ./backend
docker build -t cmbcluster-frontend ./nextjs-frontend
```

---

## 🧪 Testing

### Pre-Deployment Validation

```bash
# Validate configuration
./scripts/common/validate-config.sh gcp
./scripts/common/validate-config.sh aws

# Check prerequisites
./scripts/common/check-prerequisites.sh
```

### Post-Deployment Validation

```bash
# Health checks
kubectl get pods -n cmbcluster
kubectl get ingress -n cmbcluster
curl https://api.YOUR_DOMAIN/health

# Run E2E tests
./scripts/common/test-e2e.sh
```

**See [Testing Documentation](./docs/TESTING.md) for comprehensive test matrix.**

---

## 🔧 Configuration

### Core Settings

```bash
# Cloud provider selection
CLOUD_PROVIDER=gcp|aws

# Authentication provider selection (deployment-agnostic!)
AUTH_PROVIDER=auto|google|cognito
```

### Deployment Matrix

| Config | Cloud | Auth | Status |
|--------|-------|------|--------|
| **Default GCP** | GCP | Google OAuth | ✅ Tested |
| **Default AWS** | AWS | AWS Cognito | ✅ Tested |
| **GCP + Cognito** | GCP | AWS Cognito | ✅ Deployment-Agnostic |
| **AWS + Google** | AWS | Google OAuth | ✅ Deployment-Agnostic |
| **Multi-Provider** | Any | Both | ✅ Supported |

**See [.env.example](./.env.example) for all configuration options.**

---

## 📊 Cost Estimates

### Development Environment

| Cloud | Monthly Cost | Notes |
|-------|-------------|-------|
| **GCP** | $100-120 | 2 x e2-standard-2 nodes |
| **AWS** | $100-150 | 2 x t3.medium nodes |

### Production Environment

| Cloud | Monthly Cost | Notes |
|-------|-------------|-------|
| **GCP** | $250-400 | 3 x e2-standard-4 nodes |
| **AWS** | $300-500 | 3 x t3.large nodes |

**See deployment guides for detailed cost breakdowns and optimization tips.**

---

## 🚦 Migration

### Between Cloud Providers

CMBCluster supports migration between clouds:

```bash
# Export data from GCP
gsutil rsync -r gs://old-bucket s3://new-bucket

# Update configuration
CLOUD_PROVIDER=aws

# Deploy on AWS
./scripts/aws/setup-cluster.sh
./scripts/aws/deploy.sh
```

**See [Polycloud Architecture](./docs/ARCHITECTURE_POLYCLOUD.md#migration-strategies) for detailed migration strategies.**

---

## 🛠️ Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Pods not starting | Check `kubectl describe pod POD_NAME` |
| Auth failing | Verify OAuth credentials in `.env` |
| TLS cert not issued | Check DNS points to ingress IP/hostname |
| Storage not mounting | Verify CSI driver installed |

**See deployment guides for comprehensive troubleshooting:**
- [GCP Troubleshooting](./docs/DEPLOYMENT_GCP.md#troubleshooting)
- [AWS Troubleshooting](./docs/DEPLOYMENT_AWS.md#troubleshooting)

---

## 📁 Project Structure

```
cmbcluster/
├── backend/                    # FastAPI backend
│   ├── cloud_providers/        # Storage abstraction (GCS/S3)
│   ├── auth_providers/         # Auth abstraction (Google/Cognito)
│   ├── main.py                 # API endpoints
│   ├── pod_manager.py          # Kubernetes orchestration
│   └── config.py               # Configuration with validation
├── nextjs-frontend/            # Next.js frontend
│   └── src/app/api/auth/       # NextAuth OAuth integration
├── helm/                       # Helm charts (multi-cloud)
│   ├── values.yaml             # Cloud-specific configuration
│   └── templates/
│       ├── backend.yaml        # Backend deployment
│       ├── frontend.yaml       # Frontend deployment
│       └── serviceaccount.yaml # IAM bindings (Workload Identity/IRSA)
├── scripts/
│   ├── gcp/                    # GCP-specific scripts
│   │   ├── setup-cluster.sh
│   │   ├── build-images.sh
│   │   └── deploy.sh
│   ├── aws/                    # AWS-specific scripts
│   │   ├── setup-cluster.sh
│   │   ├── setup-cognito.sh
│   │   ├── build-images.sh
│   │   └── deploy.sh
│   └── common/                 # Cloud-agnostic scripts
│       ├── validate-config.sh
│       └── test-e2e.sh
└── docs/                       # Comprehensive documentation
    ├── DEPLOYMENT_AWS.md
    ├── DEPLOYMENT_GCP.md
    ├── ARCHITECTURE_POLYCLOUD.md
    └── TESTING.md
```

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built on the proven JupyterHub architecture pattern
- Inspired by multi-cloud best practices from AWS and GCP
- Thanks to the Kubernetes, Next.js, and FastAPI communities

---

## 📞 Support

- **Documentation**: [docs/](./docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/cmbcluster/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/cmbcluster/discussions)

---

**Made with ❤️ for the research community**

**Deploy on GCP or AWS • Migrate anytime • Zero vendor lock-in**
