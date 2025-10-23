# Scripts Directory Structure

```
scripts/
│
├── README.md                          # Main documentation for scripts
├── STRUCTURE.md                       # This file
│
├── aws/                              # AWS-specific scripts
│   ├── setup-cluster.sh              ✅ Phase 1 - Create EKS cluster and infrastructure
│   ├── cleanup.sh                    ✅ Phase 1 - Delete all AWS resources
│   ├── setup-cognito.sh              ⏳ Phase 3 - Configure Cognito authentication
│   ├── build-images.sh               ⏳ Phase 4 - Build and push images to ECR
│   └── deploy.sh                     ⏳ Phase 4 - Deploy application to EKS
│
├── gcp/                              # GCP-specific scripts
│   ├── setup-cluster.sh              ✅ Create GKE cluster and infrastructure
│   ├── cleanup.sh                    ✅ Delete all GCP resources
│   ├── build-images.sh               ✅ Build and push images to Artifact Registry
│   ├── deploy.sh                     ✅ Deploy application to GKE
│   └── add-authorized-ip.sh          ✅ Manage master authorized networks
│
└── common/                           # Cloud-agnostic scripts
    ├── build-nextjs.sh               ✅ Build Next.js frontend
    ├── build-denario.sh              ✅ Build Denario components
    ├── retag-denario.sh              ✅ Retag Denario images
    ├── generate-encryption-key.sh    ✅ Generate encryption keys
    ├── setup-production-env.sh       ✅ Production environment setup
    ├── validate-security.sh          ✅ Security validation checks
    ├── local-dev.sh                  ✅ Local development utilities
    └── force-redeploy.sh             ✅ Force redeployment
```

## Naming Convention

### Provider-Specific Scripts (aws/ and gcp/)
Scripts with the same functionality share the same name across providers:

| Function | AWS Script | GCP Script |
|----------|-----------|-----------|
| Setup Infrastructure | `aws/setup-cluster.sh` | `gcp/setup-cluster.sh` |
| Cleanup Resources | `aws/cleanup.sh` | `gcp/cleanup.sh` |
| Build Images | `aws/build-images.sh` | `gcp/build-images.sh` |
| Deploy Application | `aws/deploy.sh` | `gcp/deploy.sh` |

**Benefits:**
- Easy to understand which scripts are equivalent
- Simple to switch providers by changing directory
- Consistent mental model across cloud providers

### Common Scripts
Cloud-agnostic scripts have descriptive names indicating their function:
- `build-*.sh` - Building components
- `setup-*.sh` - Configuration and setup
- `validate-*.sh` - Validation and checks
- `*-dev.sh` - Development utilities

## Quick Reference

### For AWS Users
```bash
cd scripts/aws
./setup-cluster.sh    # Setup
./build-images.sh     # Build (Phase 4)
./deploy.sh          # Deploy (Phase 4)
./cleanup.sh         # Cleanup
```

### For GCP Users
```bash
cd scripts/gcp
./setup-cluster.sh    # Setup
./build-images.sh     # Build
./deploy.sh          # Deploy
./cleanup.sh         # Cleanup
```

### Common Tasks (Both Providers)
```bash
cd scripts/common
./build-nextjs.sh               # Build frontend
./generate-encryption-key.sh    # Generate keys
./validate-security.sh          # Security checks
./setup-production-env.sh       # Prod setup
```

## Implementation Status

✅ Complete
⏳ Planned/In Progress
❌ Not Started

### By Phase

**Phase 1: AWS Infrastructure** (✅ Complete)
- ✅ `aws/setup-cluster.sh`
- ✅ `aws/cleanup.sh`

**Phase 2: Storage Abstraction** (Next)
- Backend code changes (no new scripts)

**Phase 3: Authentication** (⏳ Planned)
- ⏳ `aws/setup-cognito.sh`

**Phase 4: Deployment** (⏳ Planned)
- ⏳ `aws/build-images.sh`
- ⏳ `aws/deploy.sh`

## Migration from Old Structure

If you have bookmarks or documentation referencing old paths:

| Old Path | New Path |
|----------|----------|
| `scripts/setup-cluster.sh` | `scripts/gcp/setup-cluster.sh` |
| `scripts/cleanup.sh` | `scripts/gcp/cleanup.sh` |
| `scripts/build-images.sh` | `scripts/gcp/build-images.sh` |
| `scripts/deploy.sh` | `scripts/gcp/deploy.sh` |
| `scripts/setup-cluster-aws.sh` | `scripts/aws/setup-cluster.sh` |
| `scripts/cleanup-aws.sh` | `scripts/aws/cleanup.sh` |

All other scripts remain in their original names under `scripts/common/`.
