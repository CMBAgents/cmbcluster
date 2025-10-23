# CMBCluster Polycloud Architecture

**Version:** 1.0
**Last Updated:** 2025-10-24
**Status:** Production Ready

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Principles](#architecture-principles)
3. [System Architecture](#system-architecture)
4. [Provider Abstraction Layers](#provider-abstraction-layers)
5. [Deployment-Agnostic Authentication](#deployment-agnostic-authentication)
6. [Cloud Provider Comparison](#cloud-provider-comparison)
7. [Configuration Management](#configuration-management)
8. [Data Flow](#data-flow)
9. [Security Model](#security-model)
10. [Performance & Scalability](#performance--scalability)
11. [Migration Strategies](#migration-strategies)

---

## Executive Summary

CMBCluster implements a **polycloud architecture** that enables deployment on multiple cloud platforms while maintaining a single codebase. The system currently supports:

- **Google Cloud Platform (GCP)**
- **Amazon Web Services (AWS)**

### Key Features

✅ **Cloud-Agnostic Application Layer**: Business logic independent of cloud provider
✅ **Provider Abstraction**: Storage and authentication abstracted via interfaces
✅ **Configuration-Driven**: Switch providers via environment variables
✅ **Deployment-Agnostic Auth**: Use any OAuth provider on any cloud
✅ **Zero Vendor Lock-In**: Freely migrate between cloud providers
✅ **Cost Optimization**: Choose best pricing for your needs

### Strategic Benefits

1. **Flexibility**: Deploy on GCP, AWS, or both
2. **Vendor Independence**: No lock-in to a single cloud
3. **Cost Control**: Leverage competitive pricing
4. **Risk Mitigation**: Multi-cloud disaster recovery
5. **Innovation**: Use best-of-breed services from each cloud

---

## Architecture Principles

### 1. Abstraction Over Duplication

Rather than maintaining separate codebases for each cloud provider, CMBCluster uses **provider-specific adapters** that implement a common interface.

**Example**: Storage operations

```python
# Single interface
class CloudStorageProvider(ABC):
    @abstractmethod
    async def create_bucket(user_id: str) -> Dict

# Multiple implementations
class GCPStorageProvider(CloudStorageProvider):
    # GCS-specific implementation

class AWSStorageProvider(CloudStorageProvider):
    # S3-specific implementation
```

### 2. Configuration-Driven Selection

Cloud provider selection happens at **deployment time** via environment variables, not at build time.

```bash
# Deploy on GCP
CLOUD_PROVIDER=gcp ./scripts/gcp/deploy.sh

# Deploy on AWS
CLOUD_PROVIDER=aws ./scripts/aws/deploy.sh
```

### 3. Kubernetes-Native Portability

The application runs on **Kubernetes**, which provides inherent portability across clouds:
- GKE (Google Kubernetes Engine) on GCP
- EKS (Elastic Kubernetes Service) on AWS

This ensures consistent behavior regardless of the underlying infrastructure.

### 4. Deployment-Agnostic Authentication

Authentication is **decoupled from infrastructure**, allowing you to use:
- Google OAuth on AWS
- AWS Cognito on GCP
- Both providers simultaneously

---

## System Architecture

### High-Level Architecture

```
┌───────────────────────────────────────────────────────┐
│                Application Layer                       │
│           (Cloud-Agnostic Business Logic)             │
│                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│
│  │   FastAPI    │  │   Next.js    │  │  Pod Manager││
│  │   Backend    │  │   Frontend   │  │             ││
│  └──────────────┘  └──────────────┘  └─────────────┘│
└───────────────────────────┬───────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
┌───────────▼──────────┐    ┌───────────────▼──────────┐
│ Provider Abstraction │    │ Provider Abstraction     │
│       Layer          │    │       Layer              │
│                      │    │                          │
│ ┌────────────────┐  │    │ ┌────────────────────┐  │
│ │ StorageProvider│  │    │ │  AuthProvider      │  │
│ │    (ABC)       │  │    │ │    (ABC)           │  │
│ └────────────────┘  │    │ └────────────────────┘  │
│         │           │    │         │               │
│    ┌────┴────┐      │    │    ┌────┴────┐          │
│    │         │      │    │    │         │          │
│ ┌──▼──┐  ┌──▼──┐   │    │ ┌──▼──┐  ┌──▼──┐       │
│ │ GCP │  │ AWS │   │    │ │Google│ │Cognito│      │
│ │ GCS │  │ S3  │   │    │ │OAuth │ │       │      │
│ └─────┘  └─────┘   │    │ └─────┘  └───────┘      │
└─────────────────────┘    └──────────────────────────┘
            │                          │
            │                          │
┌───────────▼──────────────────────────▼──────────────┐
│          Infrastructure Layer                        │
│                                                      │
│  ┌──────────────┐              ┌──────────────┐    │
│  │     GCP      │              │     AWS      │    │
│  │              │              │              │    │
│  │ GKE          │              │ EKS          │    │
│  │ GCS          │              │ S3           │    │
│  │ Artifact Reg │              │ ECR          │    │
│  │ Workload ID  │              │ IRSA         │    │
│  └──────────────┘              └──────────────┘    │
└─────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. Application Layer

**Responsibilities**:
- Business logic
- API endpoints
- User authentication
- Pod orchestration

**Cloud Independence**:
- No direct cloud SDK calls
- All cloud operations via provider interfaces
- Configuration-driven behavior

#### 2. Provider Abstraction Layer

**Storage Provider** ([backend/cloud_providers/](../backend/cloud_providers/)):
- Abstract interface: `CloudStorageProvider`
- GCP implementation: `GCPStorageProvider`
- AWS implementation: `AWSStorageProvider`
- Factory pattern: `StorageProviderFactory`

**Auth Provider** ([backend/auth_providers/](../backend/auth_providers/)):
- Abstract interface: `AuthProvider`
- Google implementation: `GoogleAuthProvider`
- Cognito implementation: `CognitoAuthProvider`
- Factory pattern: `AuthProviderFactory`

#### 3. Infrastructure Layer

**Kubernetes Abstraction**:
- Pods, Services, Deployments (cloud-agnostic)
- CSI Drivers (cloud-specific)
- IAM Bindings (cloud-specific)

**Cloud-Specific Resources**:
| Component | GCP | AWS |
|-----------|-----|-----|
| Compute | GKE | EKS |
| Storage | GCS | S3 |
| Storage Driver | GCS FUSE CSI | S3 Mountpoint CSI |
| Container Registry | Artifact Registry | ECR |
| IAM Binding | Workload Identity | IRSA |
| Load Balancer | NGINX Ingress / GCE LB | AWS Load Balancer Controller |

---

## Provider Abstraction Layers

### Storage Abstraction

#### Interface Definition

```python
# backend/cloud_providers/base.py

class CloudStorageProvider(ABC):
    """Abstract base class for cloud storage providers"""

    @abstractmethod
    async def create_bucket(self, user_id: str, **kwargs) -> Dict:
        """Create a storage bucket for a user"""
        pass

    @abstractmethod
    async def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """Delete a storage bucket"""
        pass

    @abstractmethod
    def get_fuse_volume_spec(self, bucket_name: str, mount_path: str) -> Dict:
        """Get CSI volume specification for FUSE mount"""
        pass

    @abstractmethod
    async def upload_object(self, bucket_name: str, object_name: str, content: bytes) -> bool:
        """Upload an object to bucket"""
        pass

    # ... more methods
```

#### GCP Implementation

```python
# backend/cloud_providers/gcp_provider.py

class GCPStorageProvider(CloudStorageProvider):
    def __init__(self, project_id: str, region: str):
        self.client = storage.Client(project=project_id)
        self.project_id = project_id
        self.region = region

    def get_fuse_volume_spec(self, bucket_name: str, mount_path: str) -> Dict:
        return {
            "name": "gcs-fuse-volume",
            "csi": {
                "driver": "gcsfuse.csi.storage.gke.io",
                "volumeAttributes": {
                    "bucketName": bucket_name,
                    "mountOptions": "implicit-dirs"
                }
            }
        }
```

#### AWS Implementation

```python
# backend/cloud_providers/aws_provider.py

class AWSStorageProvider(CloudStorageProvider):
    def __init__(self, region: str, account_id: str):
        self.s3_client = boto3.client('s3', region_name=region)
        self.region = region
        self.account_id = account_id

    def get_fuse_volume_spec(self, bucket_name: str, mount_path: str) -> Dict:
        return {
            "name": "s3-fuse-volume",
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

### Authentication Abstraction

#### Interface Definition

```python
# backend/auth_providers/base.py

class AuthProvider(ABC):
    """Abstract base class for authentication providers"""

    @abstractmethod
    async def validate_token(self, token: str) -> Dict:
        """Validate OAuth token and return user info"""
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> Dict:
        """Get user information from provider"""
        pass

    @abstractmethod
    def get_oauth_config(self) -> Dict:
        """Get OAuth configuration for frontend"""
        pass
```

#### Google OAuth Implementation

```python
# backend/auth_providers/google_provider.py

class GoogleAuthProvider(AuthProvider):
    async def validate_token(self, token: str) -> Dict:
        """Validate Google ID token"""
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            self.client_id
        )
        return self.normalize_user_info(idinfo)
```

#### AWS Cognito Implementation

```python
# backend/auth_providers/aws_provider.py

class CognitoAuthProvider(AuthProvider):
    async def validate_token(self, token: str) -> Dict:
        """Validate Cognito JWT token"""
        # Fetch JWKS and verify JWT
        decoded = jwt.decode(
            token,
            self.get_jwks(),
            algorithms=['RS256'],
            audience=self.client_id,
            issuer=self.issuer
        )
        return self.normalize_user_info(decoded)
```

---

## Deployment-Agnostic Authentication

### Overview

CMBCluster's authentication system is **completely decoupled from infrastructure**, enabling maximum flexibility:

```
┌────────────────────────────────────────────────┐
│        Deployment Combinations                  │
├────────────────────────────────────────────────┤
│ 1. GCP + Google OAuth     (Default for GCP)    │
│ 2. AWS + AWS Cognito      (Default for AWS)    │
│ 3. GCP + AWS Cognito      (Deployment-Agnostic)│
│ 4. AWS + Google OAuth     (Deployment-Agnostic)│
│ 5. Any + Both Providers   (Multi-Provider)     │
└────────────────────────────────────────────────┘
```

### Configuration Examples

#### Example 1: AWS Infrastructure + Google OAuth

```bash
# .env
CLOUD_PROVIDER=aws
AUTH_PROVIDER=google

# AWS infrastructure
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1
EKS_CLUSTER_NAME=cmbcluster-eks

# Google OAuth credentials
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=secret
```

**Result**: Application runs on AWS EKS with S3 storage, but users authenticate via Google OAuth.

#### Example 2: GCP Infrastructure + AWS Cognito

```bash
# .env
CLOUD_PROVIDER=gcp
AUTH_PROVIDER=cognito

# GCP infrastructure
PROJECT_ID=my-gcp-project
CLUSTER_NAME=cmbcluster
REGION=us-central1

# AWS Cognito credentials
COGNITO_USER_POOL_ID=us-east-1_XXXXX
COGNITO_CLIENT_ID=abc123
COGNITO_CLIENT_SECRET=secret
COGNITO_ISSUER=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXX
```

**Result**: Application runs on GCP GKE with GCS storage, but users authenticate via AWS Cognito.

### Provider Selection Logic

```python
# backend/auth_providers/factory.py

class AuthProviderFactory:
    @classmethod
    def detect_configured_provider(cls, settings) -> Optional[str]:
        """Detect which auth provider is configured"""

        # Priority 1: Explicit AUTH_PROVIDER setting
        if settings.auth_provider in ['google', 'cognito']:
            return settings.auth_provider

        # Priority 2: Auto-detect based on credentials
        has_google = bool(settings.google_client_id and settings.google_client_secret)
        has_cognito = bool(
            settings.cognito_user_pool_id and
            settings.cognito_client_id and
            settings.cognito_client_secret
        )

        if has_google:
            return 'google'
        if has_cognito:
            return 'cognito'

        # Priority 3: Fallback to cloud provider default
        if settings.cloud_provider == 'gcp':
            return 'google'
        elif settings.cloud_provider == 'aws':
            return 'cognito'

        return None
```

---

## Cloud Provider Comparison

### Infrastructure Parity Matrix

| Component | GCP | AWS | Implementation |
|-----------|-----|-----|----------------|
| **Kubernetes** | GKE | EKS | ✅ Full Parity |
| **Container Registry** | Artifact Registry | ECR | ✅ Full Parity |
| **Object Storage** | GCS | S3 | ✅ Full Parity |
| **Storage FUSE** | GCS FUSE CSI | Mountpoint S3 CSI | ✅ Full Parity |
| **IAM Binding** | Workload Identity | IRSA | ✅ Full Parity |
| **Load Balancer** | NGINX/GCE | AWS LB Controller | ✅ Full Parity |
| **TLS Certificates** | cert-manager | cert-manager | ✅ Full Parity |
| **Default Auth** | Google OAuth | AWS Cognito | ✅ Full Parity |

### Feature Comparison

| Feature | GCP | AWS | Notes |
|---------|-----|-----|-------|
| **Cluster Setup Time** | 15-25 min | 20-30 min | AWS slightly slower due to VPC creation |
| **Bucket Naming** | Globally unique | Globally unique | Both require DNS-compliant names |
| **FUSE Performance** | Good | Excellent | S3 Mountpoint optimized for throughput |
| **IAM Model** | Workload Identity | IRSA | Both provide pod-level permissions |
| **Cost (Dev)** | $100-120/mo | $100-150/mo | Similar pricing |
| **Cost (Prod)** | $250-400/mo | $300-500/mo | AWS slightly higher due to NAT Gateway costs |

### Storage API Comparison

| Operation | GCP API | AWS API | Abstracted Method |
|-----------|---------|---------|-------------------|
| Create Bucket | `bucket.create()` | `create_bucket()` | `create_bucket(user_id)` |
| Delete Bucket | `bucket.delete()` | `delete_bucket()` | `delete_bucket(name, force)` |
| Upload Object | `blob.upload_from_string()` | `put_object()` | `upload_object(bucket, name, content)` |
| Download Object | `blob.download_as_bytes()` | `get_object()` | `download_object(bucket, name)` |
| List Objects | `bucket.list_blobs()` | `list_objects_v2()` | `list_objects(bucket, prefix)` |
| FUSE Mount | GCS FUSE CSI | S3 CSI | `get_fuse_volume_spec(bucket)` |

### Authentication Comparison

| Feature | Google OAuth | AWS Cognito | Abstracted |
|---------|--------------|-------------|------------|
| **User Pool** | Google Accounts | Cognito User Pool | ✅ |
| **Token Type** | ID Token (JWT) | ID Token (JWT) | ✅ |
| **Validation** | `google.oauth2.id_token` | PyJWT + JWKS | ✅ |
| **User Info Endpoint** | `userinfo` API | Cognito Attributes | ✅ |
| **MFA** | Google-managed | Built-in | ✅ |
| **Password Policy** | Google-managed | Configurable | ✅ |
| **Cost** | Free | Free tier: 50K MAU | - |

---

## Configuration Management

### Environment Variables Structure

```bash
# === Core Selection ===
CLOUD_PROVIDER=gcp|aws        # Infrastructure provider
AUTH_PROVIDER=auto|google|cognito  # Authentication provider

# === GCP Configuration (if CLOUD_PROVIDER=gcp) ===
PROJECT_ID=...
CLUSTER_NAME=...
REGION=...
ZONE=...

# === AWS Configuration (if CLOUD_PROVIDER=aws) ===
AWS_ACCOUNT_ID=...
AWS_REGION=...
EKS_CLUSTER_NAME=...

# === Google OAuth (if AUTH_PROVIDER=google or auto) ===
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# === AWS Cognito (if AUTH_PROVIDER=cognito or auto) ===
COGNITO_USER_POOL_ID=...
COGNITO_CLIENT_ID=...
COGNITO_CLIENT_SECRET=...
COGNITO_ISSUER=...
```

### Configuration Validation

The backend validates configuration on startup using Pydantic validators:

```python
# backend/config.py

@model_validator(mode='after')
def validate_cloud_config(self) -> 'Settings':
    """Validate cloud-specific configuration"""
    if self.cloud_provider == 'gcp':
        if not self.project_id:
            raise ValueError("PROJECT_ID required for GCP")

    elif self.cloud_provider == 'aws':
        if not self.aws_account_id:
            raise ValueError("AWS_ACCOUNT_ID required for AWS")
        if not self.aws_region:
            raise ValueError("AWS_REGION required for AWS")

    return self

@model_validator(mode='after')
def validate_auth_config(self) -> 'Settings':
    """Validate authentication configuration"""
    has_google = bool(self.google_client_id and self.google_client_secret)
    has_cognito = bool(
        self.cognito_user_pool_id and
        self.cognito_client_id and
        self.cognito_client_secret
    )

    if self.auth_provider == 'google' and not has_google:
        raise ValueError("AUTH_PROVIDER=google requires Google OAuth credentials")

    if self.auth_provider == 'cognito' and not has_cognito:
        raise ValueError("AUTH_PROVIDER=cognito requires Cognito credentials")

    return self
```

---

## Data Flow

### User Environment Creation Flow

```
1. User clicks "Create Environment" in UI
   │
   ▼
2. Frontend sends request to Backend API
   │
   ▼
3. Backend authenticates request
   │  ├─ Google OAuth: Validate Google ID token
   │  └─ AWS Cognito: Validate Cognito JWT
   │
   ▼
4. Backend creates storage bucket
   │  ├─ GCP: GCPStorageProvider.create_bucket()
   │  │       └─ Creates GCS bucket
   │  └─ AWS: AWSStorageProvider.create_bucket()
   │          └─ Creates S3 bucket
   │
   ▼
5. Backend creates Kubernetes Pod
   │  ├─ Get FUSE volume spec from provider
   │  ├─ Add cloud-specific annotations
   │  │  ├─ GCP: gke-gcsfuse/volumes, Workload Identity
   │  │  └─ AWS: IRSA via ServiceAccount
   │  └─ Submit Pod to Kubernetes API
   │
   ▼
6. Kubernetes mounts storage via CSI driver
   │  ├─ GCP: GCS FUSE CSI Driver
   │  └─ AWS: S3 Mountpoint CSI Driver
   │
   ▼
7. Pod starts, storage mounted at /workspace
   │
   ▼
8. Backend returns environment details to Frontend
   │
   ▼
9. User can access environment
```

### Authentication Flow (Google OAuth)

```
1. User clicks "Sign in with Google"
   │
   ▼
2. Frontend redirects to Google OAuth
   │
   ▼
3. User authorizes application
   │
   ▼
4. Google redirects back with authorization code
   │
   ▼
5. NextAuth exchanges code for tokens
   │  ├─ ID Token (JWT)
   │  └─ Access Token
   │
   ▼
6. Frontend sends ID token to Backend /auth/exchange
   │
   ▼
7. Backend validates token
   │  └─ GoogleAuthProvider.validate_token()
   │      └─ google.oauth2.id_token.verify()
   │
   ▼
8. Backend creates internal JWT token
   │  ├─ Includes user_id, email, role
   │  └─ Signs with SECRET_KEY
   │
   ▼
9. Backend returns JWT to Frontend
   │
   ▼
10. Frontend stores in httpOnly cookie
    │
    ▼
11. All subsequent requests include JWT
```

### Authentication Flow (AWS Cognito)

```
1. User clicks "Sign in with Cognito"
   │
   ▼
2. Frontend redirects to Cognito Hosted UI
   │
   ▼
3. User signs in / signs up
   │
   ▼
4. Cognito redirects back with authorization code
   │
   ▼
5. NextAuth exchanges code for tokens
   │  ├─ ID Token (JWT)
   │  └─ Access Token
   │
   ▼
6. Frontend sends ID token to Backend /auth/exchange
   │
   ▼
7. Backend validates token
   │  └─ CognitoAuthProvider.validate_token()
   │      ├─ Fetch JWKS from Cognito
   │      ├─ Verify JWT signature (RS256)
   │      └─ Validate issuer and audience
   │
   ▼
8. Backend creates internal JWT token
   │
   ▼
9. Backend returns JWT to Frontend
   │
   ▼
10. Frontend stores in httpOnly cookie
```

---

## Security Model

### Multi-Layer Security

```
┌─────────────────────────────────────────────────┐
│          Layer 1: Infrastructure                 │
│  - VPC/Subnets (Private nodes)                  │
│  - Security Groups / Firewall Rules             │
│  - IAM Policies (Least Privilege)               │
└─────────────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────────────┐
│          Layer 2: Kubernetes                     │
│  - Network Policies (Pod isolation)             │
│  - RBAC (Service Account permissions)           │
│  - Pod Security Standards                       │
└─────────────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────────────┐
│          Layer 3: Application                    │
│  - OAuth 2.0 Authentication                     │
│  - JWT Token Validation                         │
│  - Rate Limiting                                │
│  - CORS Policies                                │
└─────────────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────────────┐
│          Layer 4: Data                           │
│  - TLS Encryption (in-transit)                  │
│  - Bucket Versioning (data protection)          │
│  - Access Logs (audit trail)                    │
└─────────────────────────────────────────────────┘
```

### IAM Binding Models

#### GCP: Workload Identity

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cmbcluster-ksa
  annotations:
    iam.gke.io/gcp-service-account: cmbcluster-gsa@project.iam.gserviceaccount.com

---
# Pod annotation
metadata:
  annotations:
    gke-gcsfuse/volumes: "true"
```

**Binding**:
```bash
gcloud iam service-accounts add-iam-policy-binding \
  cmbcluster-gsa@project.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:project.svc.id.goog[namespace/cmbcluster-ksa]"
```

#### AWS: IRSA (IAM Roles for Service Accounts)

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cmbcluster-ksa
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/cmbcluster-eks-workload-role
```

**Trust Policy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.region.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "oidc.eks.region.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE:sub": "system:serviceaccount:cmbcluster:cmbcluster-ksa"
      }
    }
  }]
}
```

---

## Performance & Scalability

### Kubernetes Autoscaling

Both clouds support horizontal and vertical autoscaling:

```yaml
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cmbcluster-backend
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cmbcluster-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Cluster Autoscaling**:
- GCP: GKE Cluster Autoscaler
- AWS: EKS Cluster Autoscaler

### Storage Performance

| Metric | GCS | S3 | Notes |
|--------|-----|-----|-------|
| **Read Throughput** | 5 Gbps | 5 Gbps | Similar |
| **Write Throughput** | 5 Gbps | 5 Gbps | Similar |
| **FUSE Latency** | 10-50ms | 5-30ms | S3 Mountpoint faster |
| **List Operations** | Fast | Fast | Both paginated |
| **Max Object Size** | 5 TB | 5 TB | Same |
| **Multipart Upload** | ✅ | ✅ | Both supported |

### Database Performance

CMBCluster uses SQLite on cloud storage:

- **GCS**: Database file on GCS with local caching
- **S3**: Database file on S3 with local caching

**Optimization**: Database file loaded into pod memory on startup for fast queries.

---

## Migration Strategies

### Option 1: Blue-Green Deployment

Deploy to new cloud while keeping old cloud running:

```
Day 0: Production on GCP
Day 1: Deploy to AWS (parallel)
Day 2-7: Test AWS deployment
Day 8: Switch DNS to AWS
Day 9: Monitor AWS
Day 10: Decommission GCP
```

### Option 2: Gradual Migration

Migrate users incrementally:

```
Week 1: Deploy AWS infrastructure
Week 2: Migrate 10% of users
Week 3: Migrate 25% of users
Week 4: Migrate 50% of users
Week 5: Migrate remaining users
Week 6: Decommission old infrastructure
```

### Data Migration

**User Buckets**:
- Use `gsutil rsync` (GCP → AWS)
- Use `aws s3 sync` (AWS → GCP)
- Or use `rclone` for cross-cloud sync

```bash
# GCS → S3
gsutil -m rsync -r gs://gcp-bucket s3://aws-bucket

# S3 → GCS
aws s3 sync s3://aws-bucket gs://gcp-bucket
```

**Database**:
- Export SQLite database from old cloud
- Upload to new cloud storage
- Update `DATABASE_BUCKET` configuration

---

## Conclusion

CMBCluster's polycloud architecture provides:

✅ **True cloud portability** with zero code changes
✅ **Deployment-agnostic authentication** for maximum flexibility
✅ **Provider abstraction** at storage and auth layers
✅ **Configuration-driven selection** for easy switching
✅ **Production-ready** with security best practices

The system demonstrates that **abstraction without duplication** is achievable through careful interface design and provider-specific implementations.

---

**Document Version**: 1.0
**Last Updated**: 2025-10-24
**Maintainer**: CMBCluster Team
