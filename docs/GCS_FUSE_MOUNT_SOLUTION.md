# GCS FUSE Mount Permission Error Solution

## Problem Summary

When deploying user pods with GCS FUSE-mounted storage in CMBCluster, applications were encountering permission errors:

```
PermissionError: [Errno 13] Permission denied: 'project_app'
```

### Root Causes

1. **GCS FUSE Mount Timing**: The GCS FUSE sidecar takes time to initialize and mount the storage, but applications start immediately
2. **Application-Specific Path Issues**: Some applications (like Denario) have hardcoded relative paths that don't work with dynamic mount points
3. **Permission Mismatch**: Container needs to run as uid 1000 to write to GCS FUSE mounts

## Generic Solution (Works for All Images)

### 1. Init Container for Mount Readiness

We added an init container that waits for the GCS FUSE mount to be ready before the main application starts:

```python
"initContainers": [{
    "name": "wait-for-mount",
    "image": "busybox:latest",
    "command": ["/bin/sh"],
    "args": [
        "-c",
        f"echo 'Waiting for GCS FUSE mount...'; "
        f"for i in $(seq 1 60); do "
        f"if [ -d {working_dir} ] && touch {working_dir}/.mount_test 2>/dev/null; then "
        f"rm -f {working_dir}/.mount_test; "
        f"mkdir -p {working_dir}/cmbagent_output {working_dir}/.matplotlib 2>/dev/null || true; "
        f"exit 0; fi; "
        f"sleep 2; done; "
        f"exit 1"
    ],
    "volumeMounts": [{
        "name": "user-workspace",
        "mountPath": working_dir
    }],
    "securityContext": {
        "runAsUser": 1000,
        "runAsGroup": 1000
    }
}]
```

**Benefits**:
- ✅ Generic - works with any container image
- ✅ Ensures mount is writable before app starts
- ✅ Creates necessary subdirectories
- ✅ Fails explicitly if mount doesn't become ready in 2 minutes

### 2. Working Directory Configuration

Set the container's working directory to the mount path:

```python
"workingDir": working_dir  # e.g., /project_app
```

This ensures applications start in the correct directory where storage is mounted.

### 3. Startup and Readiness Probes

Added probes to verify mount availability:

```python
"startupProbe": {
    "exec": {
        "command": ["/bin/sh", "-c", f"test -d {working_dir} && test -w {working_dir}"]
    },
    "initialDelaySeconds": 10,
    "periodSeconds": 5,
    "failureThreshold": 30  # 150 seconds total
},
"readinessProbe": {
    "exec": {
        "command": ["/bin/sh", "-c", f"test -d {working_dir} && test -w {working_dir}"]
    },
    "initialDelaySeconds": 5,
    "periodSeconds": 10,
    "failureThreshold": 3
}
```

## Application-Specific Solutions

### Denario Custom Image

For applications with hardcoded paths (like Denario's `PROJECT_DIR = "project_app"`), we created a custom image:

**Location**: `docker/denario/`

**Key Changes**:
1. Uses Denario's `--deploy` flag for dynamic directory creation
2. Runs as uid 1000 (matches GKE requirements)
3. Compatible with any mount path

**Build**:
```bash
./scripts/build-denario.sh [PROJECT_ID] [TAG] [IMAGE_REPO]
```

**Image**: `us-central1-docker.pkg.dev/PROJECT_ID/cmbcluster-dev-images/denario:latest`

## Implementation Files Changed

### backend/pod_manager.py

1. **Lines 750-767**: Added `wait-for-mount` init container
2. **Line 777**: Added `workingDir` configuration
3. **Lines 780-797**: Added startup and readiness probes
4. **Line 678**: Added `PROJECT_DIR` environment variable (for compatibility)

## Testing the Solution

### 1. Create New Environment

```bash
# Through API or frontend, create a new environment with:
# - Application: Denario (custom image)
# - Storage: Select existing or create new GCS bucket
```

### 2. Verify Pod Starts Successfully

```bash
# Get the pod name
kubectl get pods -n cmbcluster | grep user-

# Check init container completed
kubectl describe pod POD_NAME -n cmbcluster | grep -A 10 "Init Containers"

# Check main container is running
kubectl get pod POD_NAME -n cmbcluster
# Should show: Running

# Check logs for errors
kubectl logs POD_NAME -n cmbcluster
# Should NOT show: PermissionError
```

### 3. Verify Data Persistence

```bash
# Exec into pod and create a test file
kubectl exec -n cmbcluster POD_NAME -- sh -c "echo 'test' > /project_app/test.txt"

# Delete and recreate pod
# File should still exist in new pod

# Or check GCS bucket directly
gsutil ls gs://YOUR_BUCKET_NAME/
```

## Troubleshooting

### Permission Denied Errors

**Symptom**: `PermissionError: [Errno 13] Permission denied`

**Solutions**:
1. Check init container logs: `kubectl logs POD_NAME -c wait-for-mount -n cmbcluster`
2. Verify GCS FUSE mount options include `uid=1000,gid=1000`
3. Ensure pod `securityContext` has `runAsUser: 1000`
4. Check service account has `Storage Object Admin` role

### Init Container Fails

**Symptom**: Pod stuck in `Init:Error` or `Init:CrashLoopBackOff`

**Solutions**:
1. Check GCS FUSE sidecar logs: `kubectl logs POD_NAME -c gke-gcsfuse-sidecar -n cmbcluster`
2. Verify bucket exists and service account has access
3. Increase init container timeout (currently 120 seconds)
4. Check GKE cluster has GCS FUSE CSI driver enabled

### Application Still Uses Wrong Directory

**Symptom**: Application creates files in wrong location (e.g., `/app/project_app` instead of `/project_app`)

**Solutions**:
1. Use custom image with correct configuration (like Denario custom image)
2. Override application entrypoint to set working directory
3. Use environment variables to configure application's data directory

## Benefits of This Solution

1. **Generic**: Works with any Docker image without modification
2. **Reliable**: Explicit wait for mount readiness
3. **Scalable**: No performance overhead, just startup delay
4. **Debuggable**: Clear failure modes and logging
5. **Maintainable**: Clean separation of concerns

## Future Improvements

1. **Parallel Init**: If multiple checks needed, run them in parallel
2. **Health Metrics**: Export mount readiness metrics to monitoring
3. **Dynamic Timeout**: Adjust based on bucket size/location
4. **Caching**: Use local SSD for frequently accessed files
5. **Image Registry**: Auto-build custom images for popular applications

## References

- [GCS FUSE CSI Driver Documentation](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/cloud-storage-fuse-csi-driver)
- [Kubernetes Init Containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
