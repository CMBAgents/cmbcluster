# Troubleshooting Guide

Common issues and solutions for CMBCluster.

## Pod Issues

### Pods Won't Start (CrashLoopBackOff)

**Symptoms:**
```
NAME                                READY   STATUS             RESTARTS   AGE
cmbcluster-backend-abc123           0/1     CrashLoopBackOff   5          2m
```

**Diagnosis:**
```bash
# Check pod status
kubectl get pods -n cmbcluster

# Get detailed info
kubectl describe pod POD_NAME -n cmbcluster

# View logs
kubectl logs POD_NAME -n cmbcluster

# Check previous logs (if restarting)
kubectl logs POD_NAME -n cmbcluster --previous
```

**Common Causes & Solutions:**

**Image pull errors:**
```bash
# Error: ImagePullBackOff
# Solution: Verify image exists in registry
docker pull gcr.io/YOUR_PROJECT_ID/cmbcluster-backend:latest

# Check credentials
kubectl get secret docker-registry -n cmbcluster
kubectl describe secret docker-registry -n cmbcluster

# Create image pull secret
kubectl create secret docker-registry regcred \
  --docker-server=gcr.io \
  --docker-username=_json_key \
  --docker-password="$(cat ~/key.json)" \
  -n cmbcluster
```

**Insufficient resources:**
```bash
# Error: Insufficient memory, Insufficient cpu
# Solution: Check node resources
kubectl top nodes
kubectl describe nodes

# Increase resource requests/limits in helm/values.yaml
# Or add more nodes
kubectl scale nodes --replicas=5
```

**Health check failures:**
```bash
# Error: Liveness probe failed
# Solution: Check if service is responding
kubectl exec POD_NAME -n cmbcluster -- curl http://localhost:8000/health

# Increase probe timeout
# In helm/values.yaml:
# livenessProbe:
#   initialDelaySeconds: 30
#   timeoutSeconds: 10
#   periodSeconds: 10
#   failureThreshold: 3
```

**Storage mounting issues:**
```bash
# Error: Unable to mount volume, mounting error
# Solution: Check PersistentVolume and PVC
kubectl get pv
kubectl get pvc -n cmbcluster
kubectl describe pvc PVC_NAME -n cmbcluster

# Create missing PVC
kubectl apply -f k8s/pvc.yaml -n cmbcluster

# Expand volume if full
kubectl patch pvc PVC_NAME -n cmbcluster \
  -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'
```

---

## Authentication Issues

### Login Loop (Keeps Redirecting)

**Symptoms:**
- Clicking login redirects back to login page
- No error message
- Cookie keeps getting cleared

**Diagnosis:**
```bash
# Check OAuth configuration
kubectl get secret oauth-credentials -n cmbcluster -o yaml

# View backend logs for auth errors
kubectl logs -f deployment/cmbcluster-backend -n cmbcluster | grep -i auth

# Check if redirect URI is registered
# Visit Google Cloud Console > APIs & Services > Credentials
```

**Solutions:**

1. Verify redirect URIs match exactly:
   - Google Cloud Console redirect URIs (must match exactly):
     ```
     https://your-domain.com/auth/callback
     https://api.your-domain.com/auth/callback
     ```
   - Backend configuration
   - Frontend configuration

2. Check OAuth credentials:
   ```bash
   # Update credentials if they changed
   kubectl delete secret oauth-credentials -n cmbcluster
   kubectl create secret generic oauth-credentials \
     --from-literal=google_client_id=NEW_CLIENT_ID \
     --from-literal=google_client_secret=NEW_CLIENT_SECRET \
     -n cmbcluster
   
   # Restart backend
   kubectl rollout restart deployment/cmbcluster-backend -n cmbcluster
   ```

3. Clear browser cookies:
   ```
   Settings > Privacy > Cookies > cmbcluster.io > Clear
   ```

4. Check system time:
   - JWT validation requires accurate time
   - Sync time on all nodes: `ntpdate -s time.nist.gov`

### "Invalid_grant" Error

**Symptoms:**
- Error when exchanging auth code for token
- Google OAuth shows error

**Solutions:**

1. Check code expiration (code valid for 10 minutes):
   ```bash
   # Verify request is immediate after authorization
   ```

2. Verify redirect URI matches:
   ```bash
   # Must be exact match including protocol, domain, path
   https://your-domain.com/auth/callback
   # NOT: https://your-domain.com/ or http://...
   ```

3. Check clock skew:
   ```bash
   # Sync server time
   timedatectl status
   ntpdate -u pool.ntp.org
   ```

---

## Ingress & DNS Issues

### Can't Access Domain (Connection Refused)

**Symptoms:**
- `curl: (7) Failed to connect to your-domain.com port 443`
- Browser shows "This site can't be reached"

**Diagnosis:**
```bash
# Check if ingress has IP assigned
kubectl get ingress -n cmbcluster
kubectl describe ingress cmbcluster-ingress -n cmbcluster

# Check ingress controller
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx

# Test DNS resolution
nslookup your-domain.com
nslookup api.your-domain.com

# Test direct connection to ingress IP
INGRESS_IP=$(kubectl get ingress -n cmbcluster -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}')
curl -H "Host: your-domain.com" http://$INGRESS_IP
```

**Solutions:**

1. Wait for ingress IP assignment (can take 2-5 minutes):
   ```bash
   kubectl get ingress -n cmbcluster -w
   ```

2. Verify DNS records:
   ```bash
   # Get ingress IP
   kubectl get ingress -n cmbcluster -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}'
   
   # Create DNS A records in domain registrar:
   # your-domain.com -> INGRESS_IP
   # api.your-domain.com -> INGRESS_IP
   ```

3. Test before DNS propagation:
   ```bash
   # Add to /etc/hosts (Linux/macOS) or C:\Windows\System32\drivers\etc\hosts (Windows)
   INGRESS_IP your-domain.com api.your-domain.com
   
   # Test
   curl https://your-domain.com
   ```

4. Check firewall rules:
   ```bash
   # GCP: Verify firewall allows ingress traffic
   gcloud compute firewall-rules list
   gcloud compute firewall-rules describe <RULE_NAME>
   ```

### Certificate Issues (HTTPS Errors)

**Symptoms:**
- `ERR_CERT_AUTHORITY_INVALID` in browser
- `curl: (60) SSL certificate problem`
- Certificate warnings

**Diagnosis:**
```bash
# Check certificate status
kubectl get certificates -n cmbcluster
kubectl describe certificate cmbcluster-tls -n cmbcluster

# Check certificate details
kubectl get secret cmbcluster-tls -n cmbcluster -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -text -noout

# Check for errors in cert-manager logs
kubectl logs -f -n cert-manager deployment/cert-manager
kubectl logs -f -n cert-manager deployment/cert-manager-webhook
```

**Solutions:**

1. Certificate pending (normal for new domains):
   ```bash
   # Wait up to 5 minutes for automatic issuance
   kubectl describe certificate cmbcluster-tls -n cmbcluster
   
   # If stuck, delete and recreate
   kubectl delete certificate cmbcluster-tls -n cmbcluster
   kubectl delete secret cmbcluster-tls -n cmbcluster
   
   # Trigger re-creation via ingress
   kubectl delete ingress cmbcluster-ingress -n cmbcluster
   kubectl apply -f helm/templates/ingress.yaml -n cmbcluster
   ```

2. Certificate expired:
   ```bash
   # cert-manager auto-renews 30 days before expiry
   # Force renewal:
   kubectl annotate certificate cmbcluster-tls \
     cert-manager.io/issue-temporary-certificate=true \
     --overwrite -n cmbcluster
   ```

3. Wrong domain in certificate:
   ```bash
   # Verify ingress TLS section:
   # spec:
   #   tls:
   #   - hosts:
   #     - your-domain.com
   #     - api.your-domain.com
   #     secretName: cmbcluster-tls
   ```

---

## Storage Issues

### Can't Write Files (Permission Denied)

**Symptoms:**
```
Error: Permission denied: '/workspace/file.txt'
Error: Read-only file system
```

**Diagnosis:**
```bash
# Check PVC status
kubectl get pvc -n cmbcluster
kubectl describe pvc USER_PVC -n cmbcluster

# Test write access in pod
kubectl exec -it POD_NAME -n cmbcluster -- \
  touch /workspace/test.txt

# Check filesystem permissions
kubectl exec -it POD_NAME -n cmbcluster -- \
  ls -la /workspace/
```

**Solutions:**

1. Check persistent volume:
   ```bash
   # Verify PVC is bound
   kubectl get pvc -n cmbcluster
   
   # Status should be "Bound", not "Pending" or "Lost"
   ```

2. Fix permissions:
   ```bash
   # Change ownership in pod
   kubectl exec -it POD_NAME -n cmbcluster -- \
     chmod 755 /workspace/
   
   # Run as non-root might cause permission issues
   # Update pod spec to use correct user
   ```

3. Expand volume if full:
   ```bash
   # Check usage
   kubectl exec POD_NAME -n cmbcluster -- df -h /workspace/
   
   # Expand if needed
   kubectl patch pvc USER_PVC -n cmbcluster \
     -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'
   ```

### Volume Not Mounting

**Symptoms:**
```
Error: Unable to mount volume 'workspace'
```

**Diagnosis:**
```bash
# Check PVC and PV
kubectl get pv
kubectl get pvc -n cmbcluster

# Check pod events
kubectl describe pod POD_NAME -n cmbcluster
```

**Solutions:**

1. Create missing PVC:
   ```bash
   # Check if storage class exists
   kubectl get storageclass
   
   # Create PVC if missing
   kubectl apply -f - <<EOF
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: workspace-claim
     namespace: cmbcluster
   spec:
     accessModes:
       - ReadWriteOnce
     storageClassName: standard
     resources:
       requests:
         storage: 10Gi
   EOF
   ```

2. Fix storage class:
   ```bash
   # GKE: standard-rwo
   # EKS: gp2
   # AKS: default
   
   # Update helm/values.yaml with correct storage class
   kubectl patch storageclass standard \
     -p '{"provisioner":"pd.csi.storage.gke.io"}'
   ```

---

## Environment Auto-Shutdown Issues

### Pod Not Shutting Down

**Symptoms:**
- Pod running > 60 minutes (free tier)
- No warning received
- Pod should have been deleted

**Diagnosis:**
```bash
# Check auto-shutdown manager logs
kubectl logs -f deployment/cmbcluster-backend -n cmbcluster | \
  grep -i shutdown

# Check environment uptime in database
kubectl exec -it deployment/cmbcluster-backend -n cmbcluster -- \
  sqlite3 /app/data/cmbcluster.db \
  "SELECT env_id, user_id, created_at, \
    CAST((JULIANDAY('now') - JULIANDAY(created_at)) * 1440 AS INTEGER) as minutes
   FROM environments WHERE status='running';"
```

**Solutions:**

1. Check auto-shutdown is enabled:
   ```bash
   # Verify backend config
   kubectl get configmap app-config -n cmbcluster -o yaml
   
   # AUTO_SHUTDOWN_CHECK_INTERVAL_MINUTES should be set (default 5)
   ```

2. Check user tier:
   ```bash
   # Free tier users should have auto-shutdown enabled
   kubectl exec -it deployment/cmbcluster-backend -n cmbcluster -- \
     sqlite3 /app/data/cmbcluster.db \
     "SELECT id, email, subscription_tier, auto_shutdown_enabled FROM users;"
   ```

3. Manually shutdown pod:
   ```bash
   # Get pod name
   kubectl get pods -l app=user-environment -n cmbcluster
   
   # Delete pod
   kubectl delete pod POD_NAME -n cmbcluster
   ```

---

## Performance & Resource Issues

### High Memory Usage

**Symptoms:**
- Backend pod using >80% memory
- Slow response times
- Pod crashing with OOMKilled

**Diagnosis:**
```bash
# Check resource usage
kubectl top pods -n cmbcluster
kubectl top nodes

# Check pod memory details
kubectl describe pod POD_NAME -n cmbcluster

# Monitor in real-time
kubectl top pods -n cmbcluster -w
```

**Solutions:**

1. Increase resource limits:
   ```yaml
   # helm/values.yaml
   backend:
     resources:
       requests:
         memory: 512Mi
       limits:
         memory: 2Gi
   ```

2. Check for memory leaks:
   ```bash
   # Monitor memory over time
   kubectl top pod POD_NAME -n cmbcluster
   # (Repeat after 5 mins)
   
   # If increasing: memory leak, restart pod
   kubectl delete pod POD_NAME -n cmbcluster
   ```

3. Scale horizontally:
   ```bash
   # Add more backend replicas
   kubectl scale deployment cmbcluster-backend \
     --replicas=5 \
     -n cmbcluster
   ```

### High CPU Usage

**Symptoms:**
- CPU consistently > 80%
- Slow page loads
- Timeouts on requests

**Diagnosis:**
```bash
# Check CPU usage
kubectl top pods -n cmbcluster

# Identify hot pod
kubectl logs -f POD_NAME -n cmbcluster | head -20

# Check for error loops
kubectl logs POD_NAME -n cmbcluster | grep -i error | tail -10
```

**Solutions:**

1. Scale horizontally:
   ```bash
   kubectl autoscale deployment cmbcluster-backend \
     --min=2 \
     --max=10 \
     --cpu-percent=70 \
     -n cmbcluster
   ```

2. Check for infinite loops:
   ```bash
   # Look for repeated errors in logs
   kubectl logs POD_NAME -n cmbcluster | \
     sort | uniq -c | sort -rn | head -10
   ```

---

## Debug Commands

```bash
# Get all resources in namespace
kubectl get all -n cmbcluster

# Get detailed resource info
kubectl describe pod POD_NAME -n cmbcluster
kubectl describe node NODE_NAME

# Access pod shell
kubectl exec -it POD_NAME -n cmbcluster -- /bin/bash

# Copy files to/from pod
kubectl cp cmbcluster/POD_NAME:/path/to/file ./local/path
kubectl cp ./local/file cmbcluster/POD_NAME:/path/to/file

# Port forward for local access
kubectl port-forward service/cmbcluster-backend 8000:8000 -n cmbcluster
kubectl port-forward pod/POD_NAME 8000:8000 -n cmbcluster

# Check pod events
kubectl get events -n cmbcluster --field-selector involvedObject.name=POD_NAME

# Get pod logs with timestamps
kubectl logs POD_NAME -n cmbcluster --timestamps=true

# Stream logs from multiple pods
kubectl logs -f -l app=cmbcluster-backend -n cmbcluster

# Get raw pod YAML
kubectl get pod POD_NAME -n cmbcluster -o yaml

# Check RBAC permissions
kubectl auth can-i list pods --as=system:serviceaccount:cmbcluster:cmbcluster-backend -n cmbcluster

# Test network connectivity
kubectl run -it debug --image=busybox --restart=Never -- sh
# Inside: wget http://cmbcluster-backend:8000/health
```

---

## Getting Help

If you can't resolve an issue:

1. **Check logs first:**
   ```bash
   kubectl logs -f deployment/cmbcluster-backend -n cmbcluster
   kubectl logs -f deployment/cmbcluster-frontend -n cmbcluster
   ```

2. **Gather information:**
   ```bash
   # Collect diagnostics
   kubectl describe all -n cmbcluster > diagnostics.txt
   kubectl logs -f deployment/cmbcluster-backend -n cmbcluster >> diagnostics.txt
   ```

3. **Report issue:**
   - Include:
     - Error message
     - Steps to reproduce
     - `kubectl version`
     - `kubectl cluster-info`
     - Relevant logs (sanitize credentials)
   - Create issue: [GitHub Issues](https://github.com/archetana/cmbcluster/issues)
