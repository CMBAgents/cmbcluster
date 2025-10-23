# CMBCluster Scripts Directory

This directory contains all deployment and management scripts for CMBCluster, organized by cloud provider.

## Directory Structure

```
scripts/
├── aws/                    # AWS-specific scripts
│   ├── setup-cluster.sh   # Create EKS cluster and infrastructure
│   ├── cleanup.sh         # Delete all AWS resources
│   ├── build-images.sh    # Build and push images to ECR (Phase 4)
│   ├── deploy.sh          # Deploy to EKS (Phase 4)
│   └── setup-cognito.sh   # Configure Cognito auth (Phase 3)
│
├── gcp/                    # GCP-specific scripts
│   ├── setup-cluster.sh   # Create GKE cluster and infrastructure
│   ├── cleanup.sh         # Delete all GCP resources
│   ├── build-images.sh    # Build and push images to Artifact Registry
│   ├── deploy.sh          # Deploy to GKE
│   └── add-authorized-ip.sh # Add IP to master authorized networks
│
└── common/                 # Cloud-agnostic scripts
    ├── build-nextjs.sh    # Build Next.js frontend
    ├── build-denario.sh   # Build Denario components
    ├── retag-denario.sh   # Retag Denario images
    ├── generate-encryption-key.sh # Generate encryption keys
    ├── setup-production-env.sh    # Production environment setup
    ├── validate-security.sh       # Security validation checks
    ├── local-dev.sh              # Local development utilities
    └── force-redeploy.sh         # Force redeployment
```

## Quick Start

### For GCP Deployment

```bash
# 1. Set up infrastructure
./scripts/gcp/setup-cluster.sh

# 2. Build and push images
./scripts/gcp/build-images.sh

# 3. Deploy application
./scripts/gcp/deploy.sh

# Clean up everything
./scripts/gcp/cleanup.sh
```

### For AWS Deployment

```bash
# 1. Set up infrastructure (Phase 1 - COMPLETED)
./scripts/aws/setup-cluster.sh

# 2. Build and push images (Phase 4 - TODO)
./scripts/aws/build-images.sh

# 3. Deploy application (Phase 4 - TODO)
./scripts/aws/deploy.sh

# Clean up everything (Phase 1 - COMPLETED)
./scripts/aws/cleanup.sh
```

## Implementation Status

### AWS Scripts

| Script | Status | Phase | Description |
|--------|--------|-------|-------------|
| `setup-cluster.sh` | ✅ Complete | Phase 1 | Creates EKS cluster, VPC, S3, ECR, IAM roles |
| `cleanup.sh` | ✅ Complete | Phase 1 | Deletes all AWS resources |
| `setup-cognito.sh` | ⏳ Planned | Phase 3 | Sets up Cognito user pool |
| `build-images.sh` | ⏳ Planned | Phase 4 | Builds and pushes to ECR |
| `deploy.sh` | ⏳ Planned | Phase 4 | Deploys to EKS with Helm |

### GCP Scripts

| Script | Status | Description |
|--------|--------|-------------|
| `setup-cluster.sh` | ✅ Complete | Creates GKE cluster and infrastructure |
| `cleanup.sh` | ✅ Complete | Deletes all GCP resources |
| `build-images.sh` | ✅ Complete | Builds and pushes to Artifact Registry |
| `deploy.sh` | ✅ Complete | Deploys to GKE with Helm |
| `add-authorized-ip.sh` | ✅ Complete | Manages master authorized networks |

### Common Scripts

All common scripts are cloud-agnostic and work with both GCP and AWS deployments.

## Configuration

All scripts read configuration from the `.env` file in the project root. Copy `.env.example` to `.env` and configure for your cloud provider:

```bash
# Set cloud provider
CLOUD_PROVIDER=aws  # or "gcp"

# Configure provider-specific variables
# See .env.example for full configuration
```

## Script Naming Convention

- **Provider-specific scripts** share the same name across `aws/` and `gcp/` folders
  - Example: Both `aws/setup-cluster.sh` and `gcp/setup-cluster.sh` exist
  - This makes it easy to switch providers by changing the directory

- **Common scripts** have descriptive names and work with any cloud provider

## Development Workflow

### Adding a New Cloud Provider Script

1. Determine if the script is cloud-specific or common
2. Place in appropriate folder (`aws/`, `gcp/`, or `common/`)
3. Use consistent naming with existing scripts
4. Update this README with the new script
5. Add usage examples

### Updating Existing Scripts

1. Maintain backward compatibility when possible
2. Update corresponding tests
3. Update documentation in this README
4. Consider impact on both cloud providers

## Script Dependencies

### Required Tools

**For GCP:**
- `gcloud` CLI
- `kubectl`
- `helm`
- `docker`

**For AWS:**
- `aws` CLI v2
- `eksctl`
- `kubectl`
- `helm`
- `docker`

**Common:**
- `bash` 4.0+
- `jq` (for JSON processing)
- `openssl` (for key generation)

### Installation

#### macOS
```bash
# GCP tools
brew install google-cloud-sdk kubectl helm docker

# AWS tools
brew install awscli eksctl kubectl helm docker
```

#### Linux (Ubuntu/Debian)
```bash
# GCP tools
sudo apt-get install google-cloud-sdk kubectl helm docker.io

# AWS tools
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
```

#### Windows (WSL2)
Use the Linux installation instructions above in WSL2.

## Troubleshooting

### Common Issues

**Script not executable:**
```bash
chmod +x scripts/aws/*.sh
chmod +x scripts/gcp/*.sh
chmod +x scripts/common/*.sh
```

**AWS credentials not configured:**
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and default region
```

**GCP authentication not set:**
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

**kubectl context pointing to wrong cluster:**
```bash
# For GCP
gcloud container clusters get-credentials CLUSTER_NAME --zone ZONE

# For AWS
aws eks update-kubeconfig --name CLUSTER_NAME --region REGION
```

## Best Practices

1. **Always review `.env` before running scripts** - Ensure cloud provider and credentials are correct

2. **Test in development first** - Never run cleanup scripts in production without confirmation

3. **Use version control** - Commit changes to scripts with clear descriptions

4. **Document changes** - Update this README when adding or modifying scripts

5. **Handle errors gracefully** - Use `set -e` and proper error checking

6. **Make scripts idempotent** - Scripts should be safe to run multiple times

## Security Notes

- Never commit `.env` files with real credentials
- Use IAM roles and service accounts instead of static credentials when possible
- Regularly rotate access keys and secrets
- Review IAM policies for least privilege
- Enable audit logging for infrastructure changes

## Support

For issues or questions:
1. Check the main project README
2. Review the aws-integration-plan.md for architecture details
3. Check PHASE1_COMPLETION.md for implementation notes
4. Open an issue in the project repository

## Phase Implementation Roadmap

- ✅ **Phase 1**: AWS Infrastructure Foundation
  - `aws/setup-cluster.sh` - Complete
  - `aws/cleanup.sh` - Complete

- ⏳ **Phase 2**: Storage Abstraction (In Progress)
  - Backend storage provider abstraction
  - S3 provider implementation

- ⏳ **Phase 3**: Authentication Abstraction
  - `aws/setup-cognito.sh` - Planned
  - Auth provider abstraction

- ⏳ **Phase 4**: Deployment Scripts
  - `aws/build-images.sh` - Planned
  - `aws/deploy.sh` - Planned
  - Helm chart updates

---

**Last Updated:** 2025-10-23
**Maintained By:** CMBCluster Development Team
