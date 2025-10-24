# CMBCluster Polycloud Deployment Strategy

**Version:** 1.0
**Date:** 2025-10-17
**Status:** Architecture Definition Phase
**Branch:** `feature/aws-deployment`

---

## Executive Summary

This document defines the comprehensive strategy for evolving CMBCluster from a GCP-only platform to a **polycloud deployment architecture** supporting both **Google Cloud Platform (GCP)** and **Amazon Web Services (AWS)**. The implementation follows a phased approach ensuring backward compatibility while enabling cloud provider flexibility.

### Strategic Objectives

1. **Multi-Cloud Support**: Enable deployment on both GCP and AWS
2. **Provider Abstraction**: Cloud-agnostic application layer
3. **Operational Flexibility**: Switch providers via configuration
4. **Cost Optimization**: Leverage best pricing across clouds
5. **Vendor Independence**: Reduce lock-in to single provider

---

## Current Architecture Analysis

### GCP Implementation Overview

**Infrastructure Components:**
- **Kubernetes**: GKE (Google Kubernetes Engine) private clusters
- **Container Registry**: Google Artifact Registry
- **Storage**: Google Cloud Storage (GCS) with GCS FUSE CSI Driver
- **Authentication**: Google OAuth 2.0
- **Networking**: VPC, Cloud NAT, Cloud Router
- **DNS**: Google Cloud DNS
- **Load Balancing**: NGINX Ingress Controller
- **TLS**: cert-manager with Let's Encrypt
- **IAM**: Workload Identity for pod-level permissions

**Application Stack:**
- **Backend**: FastAPI (Python) with GCS SDK
- **Frontend**: Next.js with NextAuth (Google Provider)
- **Database**: SQLite on GCS bucket (versioned)
- **User Environments**: Kubernetes pods with GCS FUSE mounted storage

**Key Dependencies:**
```
Backend:
  - google-cloud-storage
  - authlib (Google OAuth)

Frontend:
  - next-auth (GoogleProvider)

Infrastructure:
  - gcsfuse.csi.storage.gke.io (FUSE driver)
  - gke.io/gcp-service-account (Workload Identity)
```

---

## Polycloud Architecture Design

### Design Principles

1. **Abstraction Over Duplication**: Single codebase with provider-specific adapters
2. **Configuration-Driven**: Cloud selection via environment variables
3. **Kubernetes-Native**: Leverage K8s portability across clouds
4. **Backwards Compatible**: GCP deployments continue unchanged
5. **Testable**: Each provider independently testable

### Architecture Layers

```
┌─────────────────────────────────────────────────┐
│           Application Layer (Cloud-Agnostic)     │
│  - FastAPI Backend                               │
│  - Next.js Frontend                              │
│  - Business Logic                                │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│      Cloud Provider Abstraction Layer           │
│  - StorageProvider (ABC)                         │
│  - AuthProvider (ABC)                            │
│  - InfraProvider (ABC)                           │
└─────────────────────────────────────────────────┘
                      ↓
        ┌─────────────────────────────┐
        │                             │
┌───────▼─────────┐         ┌────────▼──────────┐
│  GCP Provider   │         │   AWS Provider    │
│  - GCS Storage  │         │   - S3 Storage    │
│  - Google Auth  │         │   - Cognito Auth  │
│  - GKE          │         │   - EKS           │
└─────────────────┘         └───────────────────┘
```

---

## Implementation Phases

### Phase 1: AWS Infrastructure Foundation
**Duration:** 2-3 weeks
**Status:** Pending
**Branch:** `feature/aws-deployment`

#### Scope
Set up core AWS infrastructure equivalent to existing GCP setup.

#### Deliverables

**1.1 AWS Cluster Setup Script** ([scripts/setup-cluster-aws.sh](scripts/setup-cluster-aws.sh))
```bash
Components:
  - EKS cluster creation (public/private endpoints)
  - VPC with 3 AZs (public + private subnets)
  - NAT Gateway for private subnet egress
  - ECR (Elastic Container Registry) for images
  - S3 bucket for database storage
  - IAM roles and IRSA configuration
  - AWS Load Balancer Controller installation
  - cert-manager installation
  - EBS CSI Driver for persistent volumes
```

**1.2 AWS Cluster Cleanup Script** ([scripts/cleanup-aws.sh](scripts/cleanup-aws.sh))
```bash
Cleanup Order:
  1. Delete EKS node groups
  2. Delete EKS cluster
  3. Delete NAT Gateways
  4. Delete Elastic IPs
  5. Delete Subnets
  6. Delete VPC
  7. Delete S3 buckets
  8. Delete ECR repositories
  9. Delete IAM roles and policies
```

**1.3 AWS Environment Configuration**
```bash
# .env additions
CLOUD_PROVIDER=aws
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012
EKS_CLUSTER_NAME=cmbcluster-eks
ECR_REGISTRY_URL=123456789012.dkr.ecr.us-east-1.amazonaws.com
S3_DATABASE_BUCKET=cmbcluster-db-{account-id}
S3_USER_BUCKET_PREFIX=cmbcluster-user
```

#### Success Criteria
- [ ] EKS cluster operational with kubectl access
- [ ] ECR repository created and accessible
- [ ] S3 buckets created with proper IAM policies
- [ ] IRSA configured for pod-level permissions
- [ ] AWS Load Balancer Controller functional
- [ ] cert-manager issuing TLS certificates

#### Boundary Conditions
- Infrastructure only - no application deployment
- Uses default networking (no custom CIDR requirements)
- Single region deployment
- Development/staging configuration (not production-hardened)

---

### Phase 2: Storage Abstraction & S3 Integration
**Duration:** 2-3 weeks
**Status:** Pending
**Dependencies:** Phase 1 complete

#### Scope
Abstract storage layer to support both GCS and S3, implement S3 FUSE mounting.

#### Deliverables

**2.1 Storage Provider Abstraction**
```
backend/cloud_providers/
├── __init__.py
├── base.py              # Abstract base classes
├── gcp_provider.py      # GCP implementation (refactored)
├── aws_provider.py      # AWS implementation (new)
└── factory.py           # Provider factory
```

**2.2 Base Storage Provider Interface**
```python
class CloudStorageProvider(ABC):
    @abstractmethod
    async def create_bucket(user_id: str, **kwargs) -> Dict

    @abstractmethod
    async def delete_bucket(bucket_name: str, force: bool) -> bool

    @abstractmethod
    async def get_bucket_metadata(bucket_name: str) -> Dict

    @abstractmethod
    async def list_buckets(user_prefix: str) -> List[Dict]

    @abstractmethod
    def get_fuse_volume_spec(bucket_name: str, mount_path: str) -> Dict

    @abstractmethod
    async def ensure_bucket_permissions(bucket_name: str, identity: str) -> bool

    @abstractmethod
    async def upload_object(bucket_name: str, object_name: str, content: bytes) -> bool

    @abstractmethod
    async def download_object(bucket_name: str, object_name: str) -> Optional[bytes]
```

**2.3 AWS S3 Provider Implementation**

**S3 FUSE Driver Options:**
1. **Mountpoint for Amazon S3** (Recommended)
   - AWS-native, high-performance
   - CSI driver: `s3.csi.aws.com`
   - Best for large files and high throughput

2. **s3fs-fuse** (Alternative)
   - Community-maintained
   - POSIX-compatible filesystem
   - Easier setup, mature codebase

**Selected: Mountpoint for Amazon S3**

**Implementation Details:**
```python
# backend/cloud_providers/aws_provider.py
import boto3
from botocore.exceptions import ClientError

class AWSStorageProvider(CloudStorageProvider):
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.region = settings.aws_region

    def get_fuse_volume_spec(self, bucket_name: str, mount_path: str) -> Dict:
        return {
            "name": "user-workspace-fuse",
            "csi": {
                "driver": "s3.csi.aws.com",
                "volumeAttributes": {
                    "bucketName": bucket_name,
                    "region": self.region,
                    "mountOptions": "allow-delete,uid=1000,gid=1000"
                }
            }
        }
```

**2.4 Storage Manager Refactor**
```python
# backend/storage_manager.py (updated)
class StorageManager:
    def __init__(self):
        self.provider = StorageProviderFactory.create(settings.cloud_provider)

    async def create_user_bucket(self, user_id: str, **kwargs):
        return await self.provider.create_bucket(user_id, **kwargs)
```

**2.5 Kubernetes CSI Driver Installation**
```bash
# For AWS EKS
kubectl apply -k "github.com/awslabs/mountpoint-s3-csi-driver/deploy/kubernetes/overlays/stable/?ref=v1.5.0"
```

#### Success Criteria
- [ ] Both GCP and AWS providers pass unit tests
- [ ] Factory correctly selects provider based on CLOUD_PROVIDER env
- [ ] S3 FUSE CSI driver installed on EKS
- [ ] Test bucket creation/deletion on both clouds
- [ ] Pod can mount S3 bucket with FUSE and read/write files

#### Boundary Conditions
- Storage operations only (no auth or compute changes)
- Single bucket per user environment (no cross-bucket operations)
- Standard storage class (no lifecycle policies yet)
- No migration tooling between clouds

---

### Phase 3: Authentication Abstraction & AWS Cognito
**Duration:** 2 weeks
**Status:** Pending
**Dependencies:** Phase 1 complete

#### Scope
Add AWS Cognito authentication alongside Google OAuth.

#### Deliverables

**3.1 Cognito User Pool Setup**
```bash
# scripts/setup-cognito.sh
aws cognito-idp create-user-pool \
  --pool-name cmbcluster-users \
  --auto-verified-attributes email \
  --username-attributes email \
  --schema Name=email,Required=true

aws cognito-idp create-user-pool-client \
  --user-pool-id ${POOL_ID} \
  --client-name cmbcluster-web \
  --generate-secret \
  --allowed-oauth-flows authorization_code \
  --allowed-oauth-scopes openid email profile \
  --callback-urls https://${DOMAIN}/api/auth/callback/cognito
```

**3.2 Backend Auth Provider Abstraction**
```python
# backend/auth_providers/base.py
class AuthProvider(ABC):
    @abstractmethod
    async def validate_token(self, token: str) -> Dict

    @abstractmethod
    async def exchange_token(self, oauth_token: str, user_info: Dict) -> str

# backend/auth_providers/google_provider.py
class GoogleAuthProvider(AuthProvider):
    # Existing implementation

# backend/auth_providers/aws_provider.py
class AWSCognitoAuthProvider(AuthProvider):
    def __init__(self):
        self.cognito_client = boto3.client('cognito-idp')
        self.user_pool_id = settings.cognito_user_pool_id
```

**3.3 NextAuth Configuration Update**
```typescript
// nextjs-frontend/src/app/api/auth/[...nextauth]/route.ts
import CognitoProvider from 'next-auth/providers/cognito';

const providers = [];

if (process.env.GOOGLE_CLIENT_ID) {
  providers.push(GoogleProvider({...}));
}

if (process.env.COGNITO_CLIENT_ID) {
  providers.push(CognitoProvider({
    clientId: process.env.COGNITO_CLIENT_ID,
    clientSecret: process.env.COGNITO_CLIENT_SECRET,
    issuer: process.env.COGNITO_ISSUER,
  }));
}
```

**3.4 Frontend Provider Selection**
```typescript
// Dynamic sign-in page
const availableProviders = [
  ...(hasGoogle ? ['google'] : []),
  ...(hasCognito ? ['cognito'] : []),
];
```

#### Success Criteria
- [ ] Cognito user pool created and configured
- [ ] Backend validates Cognito JWT tokens
- [ ] Frontend shows available OAuth providers dynamically
- [ ] Users can sign in with Cognito on AWS deployment
- [ ] Role mapping works (first user = admin)

#### Boundary Conditions
- User accounts not synced between clouds
- Single OAuth provider per deployment
- No social identity federation beyond Google/Cognito
- Manual user pool configuration (no Terraform/CDK)

---

### Phase 4: Compute & Deployment Scripts
**Duration:** 1-2 weeks
**Status:** Pending
**Dependencies:** Phase 2, Phase 3 complete

#### Scope
AWS-specific build, deployment, and pod management.

#### Deliverables

**4.1 AWS Build Script** ([scripts/build-images-aws.sh](scripts/build-images-aws.sh))
```bash
# ECR authentication
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Build and push
docker build -t ${ECR_REGISTRY}/cmbcluster-backend:${TAG} ./backend
docker push ${ECR_REGISTRY}/cmbcluster-backend:${TAG}
```

**4.2 AWS Deployment Script** ([scripts/deploy-aws.sh](scripts/deploy-aws.sh))
```bash
# Get EKS credentials
aws eks update-kubeconfig --name ${EKS_CLUSTER_NAME} --region ${AWS_REGION}

# Deploy with Helm
helm upgrade --install cmbcluster ./helm \
  --set global.cloudProvider=aws \
  --set global.awsRegion=${AWS_REGION} \
  --set global.registryUrl=${ECR_REGISTRY} \
  --set storage.driver=s3.csi.aws.com \
  --set auth.provider=cognito \
  ...
```

**4.3 Pod Manager AWS Compatibility**
```python
# backend/pod_manager.py updates
def _build_pod_spec_with_storage(self, ...):
    if settings.cloud_provider == "gcp":
        volume_spec = self.storage_manager.provider.get_fuse_volume_spec(...)
        annotations = {
            "gke-gcsfuse/volumes": "true",
            "iam.gke.io/gcp-service-account": gsa_email
        }
    elif settings.cloud_provider == "aws":
        volume_spec = self.storage_manager.provider.get_fuse_volume_spec(...)
        annotations = {
            "eks.amazonaws.com/role-arn": role_arn
        }
```

**4.4 Helm Chart Updates**
```yaml
# helm/values.yaml
global:
  cloudProvider: gcp  # or aws

  gcp:
    projectId: ""
    workloadIdentityEmail: ""

  aws:
    region: ""
    accountId: ""
    roleArn: ""

storage:
  gcp:
    driver: gcsfuse.csi.storage.gke.io
  aws:
    driver: s3.csi.aws.com
```

**4.5 DNS Management**
```bash
# GCP: Google Cloud DNS (existing)
# AWS: Route53
aws route53 change-resource-record-sets \
  --hosted-zone-id ${ZONE_ID} \
  --change-batch file://dns-record.json
```

#### Success Criteria
- [ ] Images build and push to ECR successfully
- [ ] Helm deployment completes on EKS
- [ ] Pods mount S3 buckets correctly
- [ ] Backend pods have S3 access via IRSA
- [ ] Ingress exposes services with TLS
- [ ] End-to-end user environment creation works

#### Boundary Conditions
- Single cluster per cloud (no multi-cluster)
- Standard Kubernetes resources (no custom operators)
- Manual DNS setup (no automatic Route53 zone creation)

---

### Phase 5: Configuration Management & Documentation
**Duration:** 1 week
**Status:** Pending
**Dependencies:** Phase 1-4 complete

#### Scope
Unified configuration, environment templates, and comprehensive documentation.

#### Deliverables

**5.1 Unified Environment Configuration**
```bash
# .env.example (updated)
# === Cloud Provider Selection ===
CLOUD_PROVIDER=gcp  # gcp | aws

# === GCP Configuration (if CLOUD_PROVIDER=gcp) ===
PROJECT_ID=
CLUSTER_NAME=
REGION=us-central1
...

# === AWS Configuration (if CLOUD_PROVIDER=aws) ===
AWS_ACCOUNT_ID=
AWS_REGION=us-east-1
EKS_CLUSTER_NAME=
ECR_REGISTRY_URL=
...

# === Authentication (Provider-Specific) ===
# For GCP
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# For AWS
COGNITO_USER_POOL_ID=
COGNITO_CLIENT_ID=
COGNITO_CLIENT_SECRET=
```

**5.2 Configuration Validation**
```python
# backend/config.py (enhanced)
class Settings(BaseSettings):
    cloud_provider: Literal["gcp", "aws"] = "gcp"

    # GCP fields
    project_id: Optional[str] = None

    # AWS fields
    aws_account_id: Optional[str] = None
    aws_region: Optional[str] = None

    @validator('project_id')
    def validate_gcp_config(cls, v, values):
        if values.get('cloud_provider') == 'gcp' and not v:
            raise ValueError("PROJECT_ID required for GCP")
        return v

    @validator('aws_account_id')
    def validate_aws_config(cls, v, values):
        if values.get('cloud_provider') == 'aws' and not v:
            raise ValueError("AWS_ACCOUNT_ID required for AWS")
        return v
```

**5.3 Deployment Documentation**

**5.3.1** [DEPLOYMENT_AWS.md](docs/DEPLOYMENT_AWS.md)
- AWS prerequisites
- IAM permissions required
- Step-by-step AWS setup
- Cognito configuration
- Troubleshooting guide

**5.3.2** [DEPLOYMENT_GCP.md](docs/DEPLOYMENT_GCP.md) (updated)
- Enhanced GCP documentation
- Comparison with AWS deployment
- Migration considerations

**5.3.3** [ARCHITECTURE_POLYCLOUD.md](docs/ARCHITECTURE_POLYCLOUD.md)
- Architecture diagrams
- Provider comparison matrix
- Cost analysis
- Performance benchmarks

**5.4 Testing Documentation**
```bash
# Test matrix
- [ ] GCP deployment from scratch
- [ ] AWS deployment from scratch
- [ ] Switch GCP -> AWS (configuration only)
- [ ] User environment creation (both clouds)
- [ ] Storage operations (both clouds)
- [ ] Authentication flows (both clouds)
- [ ] TLS certificate issuance
```

#### Success Criteria
- [ ] Configuration validation prevents invalid setups
- [ ] Documentation enables fresh deployment on either cloud
- [ ] All test matrix items pass
- [ ] Migration guide drafted

#### Boundary Conditions
- Documentation in English only
- Single deployment model (no hybrid cloud)
- Manual configuration (no automation framework)

---

### Phase 6: Testing & Validation (Continuous)
**Duration:** Ongoing throughout all phases
**Status:** Active

#### Scope
Comprehensive testing across both cloud providers.

#### Test Categories

**6.1 Unit Tests**
```bash
pytest backend/tests/cloud_providers/
pytest backend/tests/storage/
pytest backend/tests/auth/
```

**6.2 Integration Tests**
```bash
# Test against live cloud resources
./scripts/test-integration-gcp.sh
./scripts/test-integration-aws.sh
```

**6.3 End-to-End Tests**
```bash
# Full user journey
- Sign up / Sign in
- Create environment
- Upload files to storage
- Execute code
- Download results
- Delete environment
```

**6.4 Performance Tests**
```bash
# Storage I/O benchmarks
- GCS FUSE vs S3 Mountpoint
- Large file transfers
- Concurrent user environments

# Cost analysis
- Compute costs (GKE vs EKS)
- Storage costs (GCS vs S3)
- Data transfer costs
```

#### Success Criteria
- [ ] 100% unit test coverage for provider abstractions
- [ ] Integration tests pass on both clouds
- [ ] E2E tests pass on both clouds
- [ ] Performance benchmarks documented
- [ ] Cost comparison documented

---

## Technical Specifications

### Cloud Provider Parity Matrix

| Component | GCP | AWS | Implementation Status |
|-----------|-----|-----|----------------------|
| **Compute** | GKE | EKS | Phase 1 |
| **Container Registry** | Artifact Registry | ECR | Phase 1 |
| **Object Storage** | GCS | S3 | Phase 2 |
| **Storage FUSE** | GCS FUSE CSI | Mountpoint S3 CSI | Phase 2 |
| **Authentication** | Google OAuth | AWS Cognito | Phase 3 |
| **IAM** | Workload Identity | IRSA | Phase 1 |
| **Load Balancer** | NGINX Ingress | AWS LB Controller | Phase 1 |
| **DNS** | Cloud DNS | Route53 | Phase 4 |
| **TLS** | cert-manager | cert-manager | Phase 1 |
| **Monitoring** | Cloud Monitoring | CloudWatch | Future |
| **Logging** | Cloud Logging | CloudWatch Logs | Future |

### Configuration Schema

```json
{
  "cloud": {
    "provider": "gcp | aws",
    "gcp": {
      "projectId": "string",
      "region": "string",
      "zone": "string",
      "clusterName": "string",
      "artifactRegistry": "string",
      "workloadIdentity": {
        "serviceAccount": "string"
      }
    },
    "aws": {
      "accountId": "string",
      "region": "string",
      "eksClusterName": "string",
      "ecrRegistry": "string",
      "irsa": {
        "roleArn": "string"
      }
    }
  },
  "storage": {
    "driver": "gcsfuse.csi.storage.gke.io | s3.csi.aws.com",
    "class": "STANDARD | STANDARD_IA",
    "bucketPrefix": "string"
  },
  "auth": {
    "provider": "google | cognito",
    "google": {
      "clientId": "string",
      "clientSecret": "string"
    },
    "cognito": {
      "userPoolId": "string",
      "clientId": "string",
      "clientSecret": "string",
      "issuer": "string"
    }
  }
}
```

---

## Migration Strategy

### Existing Deployments
- **No changes required** - GCP deployments continue to work
- Opt-in to AWS via configuration
- No data migration tooling (initial release)

### New Deployments
- Select cloud provider during setup
- Follow provider-specific guide
- Configuration-driven setup

### Future: Multi-Cloud Operations
- Active-active across clouds (future phase)
- Cross-cloud data replication (future phase)
- Unified management dashboard (future phase)

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| S3 FUSE performance | Medium | High | Benchmark early, document limitations |
| AWS cost variance | Low | Medium | Cost calculator, budget alerts |
| Auth provider parity | Low | Medium | Comprehensive testing |
| Incomplete abstraction | Medium | High | Code reviews, interface contracts |
| Configuration complexity | High | Medium | Validation, documentation |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Support overhead (2 clouds) | High | Medium | Unified tooling, automation |
| Knowledge distribution | Medium | Medium | Documentation, runbooks |
| Testing complexity | High | Low | CI/CD matrix testing |
| Deployment errors | Medium | High | Validation scripts, dry-run mode |

---

## Success Metrics

### Phase Completion Metrics
- [ ] All phase deliverables completed
- [ ] Test coverage > 80%
- [ ] Documentation peer-reviewed
- [ ] Demo deployment successful

### Production Readiness
- [ ] Zero-downtime GCP deployments maintained
- [ ] AWS deployment completes in < 30 minutes
- [ ] User environment creation < 60 seconds (both clouds)
- [ ] Cost variance within 20% between clouds

---

## Dependencies & Prerequisites

### Development Environment
```bash
Required:
  - kubectl (1.28+)
  - helm (3.12+)
  - docker (24+)
  - gcloud CLI (latest)
  - aws CLI v2 (latest)
  - Python 3.11+
  - Node.js 20+

Optional:
  - k9s (cluster management)
  - kubectx (context switching)
  - terraform (future IaC)
```

### Cloud Accounts
```
GCP:
  - Project with billing enabled
  - APIs: GKE, Artifact Registry, GCS, IAM
  - Service account with Owner role

AWS:
  - Account with billing enabled
  - IAM user with AdministratorAccess (or scoped permissions)
  - Services: EKS, ECR, S3, Cognito, VPC
```

---

## Timeline & Milestones

```
Phase 1: AWS Infrastructure        [Weeks 1-3]
  ├─ EKS cluster setup             Week 1
  ├─ IAM & IRSA configuration      Week 2
  └─ Load balancer & TLS           Week 3

Phase 2: Storage Abstraction       [Weeks 4-6]
  ├─ Provider abstraction layer    Week 4
  ├─ AWS S3 provider impl          Week 5
  └─ S3 FUSE integration          Week 6

Phase 3: Authentication            [Weeks 7-8]
  ├─ Cognito setup                Week 7
  └─ NextAuth integration         Week 8

Phase 4: Deployment Scripts        [Weeks 9-10]
  ├─ AWS build scripts            Week 9
  └─ Helm chart updates           Week 10

Phase 5: Documentation            [Week 11]
  └─ Comprehensive docs           Week 11

Phase 6: Testing (Continuous)     [Weeks 1-11]
  └─ Ongoing validation           Weekly

Total Duration: ~11 weeks
```

---

## Appendix

### Glossary

| Term | Definition |
|------|------------|
| **FUSE** | Filesystem in Userspace - allows mounting cloud storage as local filesystem |
| **CSI** | Container Storage Interface - Kubernetes standard for storage drivers |
| **IRSA** | IAM Roles for Service Accounts - AWS equivalent to Workload Identity |
| **Workload Identity** | GCP mechanism for pod-level IAM permissions |
| **Polycloud** | Architecture supporting multiple cloud providers |

### References

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Mountpoint for S3](https://github.com/awslabs/mountpoint-s3)
- [GCS FUSE CSI Driver](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/cloud-storage-fuse-csi-driver)
- [AWS Cognito](https://docs.aws.amazon.com/cognito/)
- [NextAuth.js](https://next-auth.js.org/)

### Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-17 | Claude | Initial architecture definition |

---

**Document Status:** ✅ **APPROVED FOR IMPLEMENTATION**

**Next Steps:**
1. Review and approve architecture
2. Begin Phase 1 implementation
3. Weekly progress check-ins
4. Document lessons learned

**Questions & Clarifications:**
- [ ] S3 FUSE driver: Mountpoint vs s3fs-fuse decision confirmed?
- [ ] AWS region selection: us-east-1 or other?
- [ ] Multi-tenancy model: shared cluster or dedicated per-user?
- [ ] Cost budget allocation: development vs production

---

