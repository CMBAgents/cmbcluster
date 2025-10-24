# Deployment-Agnostic Authentication Guide

**CMBCluster Phase 3 Enhancement**

---

## Overview

CMBCluster now supports **deployment-agnostic authentication**, allowing you to use any OAuth provider on any cloud platform. This means you can:

✅ Use Google OAuth on AWS deployments
✅ Use AWS Cognito on GCP deployments
✅ Switch authentication providers without changing infrastructure
✅ Support multiple authentication providers simultaneously

---

## Why Deployment-Agnostic Authentication?

### Traditional Approach (Cloud-Locked)
```
GCP Deployment → Must use Google OAuth
AWS Deployment → Must use AWS Cognito
```

**Problems:**
- Locked into cloud provider's identity service
- Difficult to maintain consistent user experience across clouds
- Cannot leverage existing OAuth setup when switching clouds
- Multi-cloud deployments require managing multiple identity systems

### CMBCluster Approach (Deployment-Agnostic)
```
Any Cloud Platform → Choose Any OAuth Provider
```

**Benefits:**
- ✅ **Flexibility**: Choose the best OAuth provider for your needs
- ✅ **Consistency**: Maintain the same user experience across clouds
- ✅ **Migration**: Keep existing user accounts when switching clouds
- ✅ **Multi-Cloud**: Use same identity provider across all deployments
- ✅ **Cost**: Use free Google OAuth instead of paid Cognito on AWS

---

## Configuration

### AUTH_PROVIDER Environment Variable

```bash
# Authentication provider selection (deployment-agnostic)
# Options: "auto", "google", "cognito"
AUTH_PROVIDER=auto
```

**Options:**

| Value | Behavior |
|-------|----------|
| `auto` | Automatically detect based on available credentials (default) |
| `google` | Force Google OAuth regardless of cloud platform |
| `cognito` | Force AWS Cognito regardless of cloud platform |

### Priority System

The authentication provider is selected using a 3-tier priority system:

```
Priority 1: AUTH_PROVIDER setting (highest)
    ↓ (if AUTH_PROVIDER=auto)
Priority 2: Available credentials (auto-detect)
    ↓ (if no credentials found)
Priority 3: CLOUD_PROVIDER setting (fallback)
```

---

## Use Cases

### Use Case 1: AWS Deployment with Google OAuth

**Scenario**: You're deploying on AWS EKS but want to use Google OAuth for authentication.

**Benefits**:
- Free tier (vs Cognito costs after 50K MAU)
- Existing Google Workspace integration
- Familiar user experience

**Configuration**:
```bash
# .env
CLOUD_PROVIDER=aws
AUTH_PROVIDER=google

# AWS infrastructure
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1
EKS_CLUSTER_NAME=cmbcluster-eks

# Google OAuth (works on AWS!)
GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
```

**Setup**:
```bash
# 1. Set up AWS infrastructure
./scripts/aws/setup-cluster.sh

# 2. Configure Google OAuth credentials in .env
# (Get from Google Cloud Console)

# 3. Deploy
./scripts/aws/deploy.sh
```

---

### Use Case 2: GCP Deployment with AWS Cognito

**Scenario**: You're deploying on GCP GKE but want to use AWS Cognito for centralized identity management.

**Benefits**:
- Centralized user management across multiple apps
- Advanced features (MFA, custom auth flows)
- Fine-grained password policies

**Configuration**:
```bash
# .env
CLOUD_PROVIDER=gcp
AUTH_PROVIDER=cognito

# GCP infrastructure
PROJECT_ID=my-gcp-project
CLUSTER_NAME=cmbcluster
REGION=us-central1

# AWS Cognito (works on GCP!)
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_CLIENT_ID=abc123
COGNITO_CLIENT_SECRET=secret
COGNITO_ISSUER=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX
```

**Setup**:
```bash
# 1. Set up GCP infrastructure
./scripts/gcp/setup-cluster.sh

# 2. Create Cognito User Pool
./scripts/aws/setup-cognito.sh

# 3. Add Cognito configuration to .env

# 4. Deploy
./scripts/gcp/deploy.sh
```

---

### Use Case 3: Multi-Provider Setup

**Scenario**: You want to offer both Google and Cognito sign-in options to your users.

**Benefits**:
- User choice (Google for consumers, Cognito for enterprise)
- Redundancy (if one provider has issues)
- Gradual migration between providers

**Configuration**:
```bash
# .env
AUTH_PROVIDER=auto  # Auto-detect both

# Configure both providers
GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret

COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_CLIENT_ID=abc123
COGNITO_CLIENT_SECRET=secret
COGNITO_ISSUER=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX
```

**Result**:
- NextAuth shows both "Sign in with Google" and "Sign in with Cognito" buttons
- Users can choose their preferred authentication method
- Backend handles both providers seamlessly

---

### Use Case 4: Cloud Migration with Consistent Auth

**Scenario**: You're migrating from GCP to AWS but want to keep using Google OAuth.

**Benefits**:
- Zero user disruption (same login experience)
- No user account migration needed
- Gradual infrastructure migration

**Migration Path**:

```bash
# Step 1: Current GCP deployment
CLOUD_PROVIDER=gcp
AUTH_PROVIDER=google
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Step 2: Set up AWS infrastructure
./scripts/aws/setup-cluster.sh

# Step 3: Deploy on AWS with same Google OAuth
CLOUD_PROVIDER=aws
AUTH_PROVIDER=google
GOOGLE_CLIENT_ID=...  # Same credentials!
GOOGLE_CLIENT_SECRET=...

# Step 4: Update DNS to point to AWS
# Users continue using Google OAuth seamlessly
```

---

## Configuration Examples

### Example 1: Default Behavior (Auto-Detect)

```bash
# .env - GCP with Google OAuth
CLOUD_PROVIDER=gcp
AUTH_PROVIDER=auto  # Optional, this is the default
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
# Result: Uses Google OAuth (auto-detected)
```

```bash
# .env - AWS with Cognito
CLOUD_PROVIDER=aws
AUTH_PROVIDER=auto  # Optional, this is the default
COGNITO_USER_POOL_ID=...
COGNITO_CLIENT_ID=...
COGNITO_CLIENT_SECRET=...
COGNITO_ISSUER=...
# Result: Uses Cognito (auto-detected)
```

### Example 2: Explicit Provider Selection

```bash
# .env - Force Google OAuth on AWS
CLOUD_PROVIDER=aws
AUTH_PROVIDER=google  # Explicit selection
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
# Result: Uses Google OAuth (explicitly configured)
```

```bash
# .env - Force Cognito on GCP
CLOUD_PROVIDER=gcp
AUTH_PROVIDER=cognito  # Explicit selection
COGNITO_USER_POOL_ID=...
COGNITO_CLIENT_ID=...
COGNITO_CLIENT_SECRET=...
COGNITO_ISSUER=...
# Result: Uses Cognito (explicitly configured)
```

### Example 3: Multi-Provider

```bash
# .env - Both providers available
CLOUD_PROVIDER=aws
AUTH_PROVIDER=auto

# Google OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# AWS Cognito
COGNITO_USER_POOL_ID=...
COGNITO_CLIENT_ID=...
COGNITO_CLIENT_SECRET=...
COGNITO_ISSUER=...

# Result: Both providers available in UI
# Backend auto-selects Google (first available)
# Frontend shows both sign-in options
```

---

## Technical Details

### Backend Provider Selection

The `AuthProviderFactory` implements the priority system:

```python
# backend/auth_providers/factory.py

@staticmethod
def create_from_config(settings) -> AuthProvider:
    # Priority 1: Explicit AUTH_PROVIDER
    if settings.auth_provider != "auto":
        if settings.auth_provider == "google":
            return GoogleAuthProvider(...)
        elif settings.auth_provider == "cognito":
            return CognitoAuthProvider(...)

    # Priority 2: Auto-detect credentials
    if settings.google_client_id:
        return GoogleAuthProvider(...)
    if settings.cognito_user_pool_id:
        return CognitoAuthProvider(...)

    # Priority 3: Fallback to CLOUD_PROVIDER
    if settings.cloud_provider == "gcp":
        return GoogleAuthProvider(...)
    elif settings.cloud_provider == "aws":
        return CognitoAuthProvider(...)
```

### Frontend Provider Detection

NextAuth dynamically builds the provider array:

```typescript
// nextjs-frontend/src/app/api/auth/[...nextauth]/route.ts

const providers: any[] = [];

// Add Google if configured
if (process.env.GOOGLE_CLIENT_ID) {
    providers.push(GoogleProvider({...}));
}

// Add Cognito if configured
if (process.env.COGNITO_CLIENT_ID) {
    providers.push(CognitoProvider({...}));
}
```

---

## Migration Guide

### Migrating from Cloud-Locked to Deployment-Agnostic

**Existing deployments continue to work unchanged!**

#### GCP Deployments (Using Google OAuth)

**Before** (implicit):
```bash
CLOUD_PROVIDER=gcp
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
# Provider: Google (auto-selected based on CLOUD_PROVIDER)
```

**After** (explicit, recommended):
```bash
CLOUD_PROVIDER=gcp
AUTH_PROVIDER=google  # NEW: Explicit selection
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
# Provider: Google (explicitly configured)
```

**No changes required** - both configurations work identically!

#### AWS Deployments (Using Cognito)

**Before** (implicit):
```bash
CLOUD_PROVIDER=aws
COGNITO_USER_POOL_ID=...
COGNITO_CLIENT_ID=...
COGNITO_CLIENT_SECRET=...
COGNITO_ISSUER=...
# Provider: Cognito (auto-selected based on CLOUD_PROVIDER)
```

**After** (explicit, recommended):
```bash
CLOUD_PROVIDER=aws
AUTH_PROVIDER=cognito  # NEW: Explicit selection
COGNITO_USER_POOL_ID=...
COGNITO_CLIENT_ID=...
COGNITO_CLIENT_SECRET=...
COGNITO_ISSUER=...
# Provider: Cognito (explicitly configured)
```

**No changes required** - both configurations work identically!

---

## Best Practices

### 1. Use Explicit AUTH_PROVIDER in Production

**Recommended**:
```bash
AUTH_PROVIDER=google  # Explicit and clear
```

**Avoid**:
```bash
AUTH_PROVIDER=auto  # Implicit, may change if credentials added
```

### 2. Document Your Choice

Add comments to your .env file:
```bash
# We use Google OAuth on AWS for cost savings and
# integration with our existing Google Workspace
AUTH_PROVIDER=google
GOOGLE_CLIENT_ID=...
```

### 3. Test Before Switching

When changing providers:
1. Test in staging environment first
2. Verify user creation and role assignment
3. Check token refresh functionality
4. Test logout behavior

### 4. Monitor Provider Selection

Check application logs on startup:
```
[INFO] AUTH_PROVIDER explicitly set to: google
[INFO] Creating Google OAuth provider (explicitly configured)
[INFO] Google OAuth provider initialized
```

---

## Troubleshooting

### Issue: "No authentication provider configured"

**Cause**: Neither Google nor Cognito credentials are configured.

**Solution**: Add credentials for at least one provider:
```bash
# Option 1: Google OAuth
GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret

# Option 2: AWS Cognito
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_CLIENT_ID=abc123
COGNITO_CLIENT_SECRET=secret
COGNITO_ISSUER=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX
```

### Issue: "Invalid AUTH_PROVIDER: xyz"

**Cause**: AUTH_PROVIDER set to invalid value.

**Solution**: Use valid option:
```bash
AUTH_PROVIDER=auto     # Auto-detect
AUTH_PROVIDER=google   # Force Google
AUTH_PROVIDER=cognito  # Force Cognito
```

### Issue: Wrong provider selected with AUTH_PROVIDER=auto

**Cause**: Multiple providers configured, auto-select picks first available.

**Solution**: Use explicit AUTH_PROVIDER:
```bash
AUTH_PROVIDER=cognito  # Force Cognito instead of auto-detected Google
```

---

## Summary

**Deployment-agnostic authentication** is a major enhancement that decouples your authentication choice from your cloud infrastructure choice. This provides:

✅ **Maximum Flexibility**: Choose any OAuth provider on any cloud
✅ **Easy Migration**: Keep auth consistent during cloud migration
✅ **Cost Optimization**: Use free Google OAuth on AWS
✅ **Multi-Cloud**: Same identity provider across all deployments
✅ **Backward Compatible**: Existing deployments work unchanged

**Key Takeaway**: You now have complete freedom to choose your authentication provider independently of your cloud platform!

---

**Related Documentation:**
- [PHASE3_COMPLETION.md](PHASE3_COMPLETION.md) - Complete Phase 3 implementation details
- [.env.example](.env.example) - Configuration examples and templates
- [backend/auth_providers/factory.py](backend/auth_providers/factory.py) - Provider selection logic
