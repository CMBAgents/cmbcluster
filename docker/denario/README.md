# Custom Denario Image for CMBCluster

This directory contains a custom Denario Docker image optimized for CMBCluster's dynamic mount path architecture.

## Why a Custom Image?

The original Denario image has a hardcoded relative path `PROJECT_DIR = "project_app"` which doesn't work well with dynamic GCS FUSE mounts at different paths (e.g., `/project_app`, `/cmbagent`, etc.).

This custom image uses Denario's built-in `--deploy` flag which enables dynamic project directory creation, making it compatible with any mount path.

## Key Differences from Original

1. **Deploy Mode Enabled**: Runs with `--deploy` flag to use `get_project_dir()` function
2. **User ID 1000**: Matches GKE pod security context requirements
3. **Dynamic Directories**: Creates temporary project directories instead of using hardcoded paths
4. **Port 8501**: Uses Streamlit's default port (configurable)

## Building the Image

### Using the dedicated script:
```bash
./scripts/build-denario.sh [PROJECT_ID] [TAG] [IMAGE_REPO]
```

### Using the main build script:
```bash
# Edit scripts/build-images.sh and add "denario" to SERVICES array
SERVICES=("denario")
./scripts/build-images.sh [PROJECT_ID] [TAG] [IMAGE_REPO]
```

### Manual build:
```bash
cd docker/denario
docker build -t denario:latest .
docker tag denario:latest YOUR_REGISTRY/denario:latest
docker push YOUR_REGISTRY/denario:latest
```

## Using the Image

### In Application Configuration

When creating an application in CMBCluster admin panel, set:
- **Image Path**: `us-central1-docker.pkg.dev/YOUR_PROJECT/cmbcluster-images/denario:latest`
- **Port**: `8501`
- **Working Directory**: `/project_app` (or any path you prefer)

### The Generic Solution

This image works with CMBCluster's generic mount initialization:

1. **Init Container**: Waits for GCS FUSE mount to be ready (up to 2 minutes)
2. **Working Directory**: Set via `workingDir` in pod spec
3. **Dynamic Creation**: Denario creates project directories on-the-fly in the mounted volume

## How It Works

```
Pod Lifecycle:
1. GCS FUSE sidecar mounts bucket → /project_app
2. Init container waits for mount to be writable
3. Init container creates necessary subdirectories
4. Main container starts with workingDir=/project_app
5. Denario runs with --deploy flag
6. Denario calls get_project_dir() which creates temp dirs in mounted volume
7. Application runs successfully with persistent storage
```

## Benefits

✅ **Generic**: Works with any mount path
✅ **No Runtime Patching**: Clean solution using Denario's built-in features
✅ **Persistent Storage**: All data stored in GCS bucket
✅ **Multi-tenant**: Each user gets isolated environment
✅ **Scalable**: No hardcoded paths or dependencies

## Testing

After deploying, verify:

1. Pod starts successfully without permission errors
2. Files created by Denario appear in GCS bucket
3. Application works normally at the ingress URL
4. Data persists across pod restarts

## Troubleshooting

### Permission Denied Errors
- Check that `runAsUser: 1000` is set in pod spec
- Verify GCS FUSE mount options include `uid=1000,gid=1000`
- Ensure init container completes successfully

### Mount Not Ready
- Increase init container timeout (currently 120 seconds)
- Check GCS FUSE sidecar logs: `kubectl logs POD_NAME -c gke-gcsfuse-sidecar`
- Verify service account has Storage Object Admin permissions

### Application Errors
- Check application logs: `kubectl logs POD_NAME`
- Verify environment variables are set correctly
- Check that working directory is writable: `kubectl exec POD_NAME -- test -w /project_app`
