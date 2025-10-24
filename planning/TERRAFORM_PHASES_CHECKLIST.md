# CMBCluster Terraform Implementation - Phase Checklist

**Status:** 📋 Ready for Kickoff
**Total Phases:** 6 (0-5)
**Duration:** 4 weeks
**Last Updated:** 2025-10-24

---

## 🗓️ Phase Timeline

```
WEEK 1                          WEEK 2                         WEEK 3-4
Days 1-3   Days 4-7  Days 8-11  Days 12-15 Days 16-19 Days 20-21 Days 22-28
Phase 0    Phase 1   Phase 2    Phase 3    Phase 4    Phase 5    Stabilize
Prep       VPC+EKS   S3+IAM     K8s+App    GCP Val    Cutover    Monitor

███░░░░░░░ ░░░░░░░░░░ ░░░░░░░░░░ ░░░░░░░░░░ ░░░░░░░░░░ ░░░░░░░░░░ ░░░░░░░░░░
Pending    Pending    Pending    Pending    Pending    Pending    Pending
```

---

## 📋 PHASE 0: Preparation & Setup (Days 1-3)

**Owner:** Lead Engineer
**Reviewer:** DevOps Lead
**Status:** ⏳ Pending Kickoff

### 0.1 Environment Preparation

- [ ] **0.1.1 AWS Account Setup**
  - [ ] Verify IAM permissions
  - [ ] Create IAM service account
  - [ ] Generate access keys
  - [ ] Configure AWS CLI
  - [ ] Test access: `aws sts get-caller-identity`
  - **Checkpoint:** AWS credentials working ✓

- [ ] **0.1.2 GCP Account Setup**
  - [ ] Verify project access
  - [ ] Create service account
  - [ ] Create service account key
  - [ ] Configure gcloud
  - [ ] Set default project
  - **Checkpoint:** GCP credentials working ✓

- [ ] **0.1.3 Tools Installation**
  - [ ] Terraform (>= 1.5.0)
  - [ ] kubectl
  - [ ] Helm 3
  - [ ] AWS CLI v2
  - [ ] Google Cloud CLI
  - **Checkpoint:** All tools verified ✓

### 0.2 Repository Setup

- [ ] **0.2.1 Git Configuration**
  - [ ] Create feature branch: `feature/terraform-implementation`
  - [ ] Commit Terraform files
  - [ ] Push to origin
  - [ ] Create branch protection rules
  - **Checkpoint:** Branch ready ✓

- [ ] **0.2.2 Documentation**
  - [ ] Copy implementation guides
  - [ ] Create runbook directory
  - [ ] Review with team
  - **Checkpoint:** Documentation in place ✓

### 0.3 State Management

- [ ] **0.3.1 AWS S3 Backend**
  - [ ] Create S3 bucket
  - [ ] Enable versioning
  - [ ] Enable encryption
  - [ ] Block public access
  - [ ] Create DynamoDB locks table
  - **Checkpoint:** S3 backend ready ✓

- [ ] **0.3.2 GCP GCS Backend**
  - [ ] Create GCS bucket
  - [ ] Enable versioning
  - [ ] Set uniform access
  - [ ] Configure lifecycle
  - **Checkpoint:** GCS backend ready ✓

### 0.4 Local Development

- [ ] **0.4.1 Terraform Init**
  - [ ] Run `terraform init`
  - [ ] Validate syntax
  - [ ] Format code
  - [ ] Optional: Run tflint
  - **Checkpoint:** Terraform validated ✓

- [ ] **0.4.2 Create Variables File**
  - [ ] Copy `dev.tfvars` template
  - [ ] Fill in local values
  - [ ] Validate no hardcoded secrets
  - **Checkpoint:** Variables configured ✓

### 0.5 Team Training

- [ ] **0.5.1 Documentation Review**
  - [ ] Engineer reads guide (1 hour)
  - [ ] Review module structure (30 min)
  - [ ] Understand state management (30 min)
  - **Checkpoint:** Engineer trained ✓

- [ ] **0.5.2 Team Walkthrough**
  - [ ] Architecture presentation (1 hour)
  - [ ] Q&A session (30 min)
  - [ ] Backup and rollback review (30 min)
  - **Checkpoint:** Team trained ✓

**Phase 0 Complete When:**
- ✅ All tools installed and verified
- ✅ Git branch created and ready
- ✅ State backends configured
- ✅ Terraform initialized
- ✅ Team trained
- ✅ Sign-off from DevOps lead

---

## 🔨 PHASE 1: Core AWS Infrastructure (Days 4-7)

**Owner:** Lead Engineer
**Reviewer:** DevOps Lead
**Status:** ⏳ Pending

### 1.1 VPC Deployment

- [ ] **1.1.1 Plan VPC**
  - [ ] Run `terraform plan -target=module.aws_vpc`
  - [ ] Review plan (3 public subnets, 3 private subnets)
  - [ ] Verify NAT Gateway configuration
  - [ ] Checkpoint: Plan reviewed ✓

- [ ] **1.1.2 Apply VPC**
  - [ ] Run `terraform apply`
  - [ ] Wait for VPC creation (~5 min)
  - [ ] Verify all subnets created
  - [ ] Checkpoint: VPC created ✓

- [ ] **1.1.3 Validate Network**
  - [ ] Verify VPC ID: `aws ec2 describe-vpcs`
  - [ ] Verify subnets: `aws ec2 describe-subnets`
  - [ ] Check NAT Gateway: `aws ec2 describe-nat-gateways`
  - [ ] Verify route tables configured
  - [ ] Checkpoint: Network validated ✓

### 1.2 EKS Cluster Deployment

- [ ] **1.2.1 Plan EKS**
  - [ ] Run `terraform plan -target=module.aws_eks`
  - [ ] Review cluster configuration
  - [ ] Verify node group settings (1-3 nodes)
  - [ ] Checkpoint: Plan reviewed ✓

- [ ] **1.2.2 Apply EKS**
  - [ ] Run `terraform apply`
  - [ ] Wait for cluster creation (~15-20 min)
  - [ ] Monitor: `watch aws eks describe-cluster`
  - [ ] Checkpoint: EKS cluster created ✓

- [ ] **1.2.3 Configure kubectl**
  - [ ] Run kubeconfig command from Terraform
  - [ ] Verify access: `kubectl cluster-info`
  - [ ] Check nodes: `kubectl get nodes`
  - [ ] Wait for nodes to be Ready (~5 min)
  - [ ] Checkpoint: kubectl access verified ✓

- [ ] **1.2.4 Validate OIDC**
  - [ ] Check OIDC provider: `aws iam list-open-id-connect-providers`
  - [ ] Verify thumbprint configured
  - [ ] Checkpoint: OIDC ready for IRSA ✓

### 1.3 Testing & Validation

- [ ] **1.3.1 Cluster Health**
  - [ ] `kubectl cluster-info` → Available ✓
  - [ ] `kubectl get nodes` → Ready ✓
  - [ ] `kubectl get pods -A` → All running ✓

- [ ] **1.3.2 State Validation**
  - [ ] `terraform state list` shows all resources
  - [ ] `terraform state validate` passes
  - [ ] State file size reasonable
  - [ ] Checkpoint: State validated ✓

- [ ] **1.3.3 Documentation**
  - [ ] Save outputs: `terraform output -json > phase1-outputs.json`
  - [ ] Save kubeconfig
  - [ ] Record cluster details
  - [ ] Checkpoint: Documented ✓

### 1.4 Rollback Test

- [ ] **1.4.1 Test Destroy Plan**
  - [ ] Run `terraform plan -destroy`
  - [ ] Review destruction order
  - [ ] DO NOT APPLY (just verify works)
  - [ ] Checkpoint: Rollback verified ✓

**Phase 1 Sign-Off:**
- ✅ EKS cluster operational
- ✅ kubectl access verified
- ✅ OIDC provider configured
- ✅ All validation passed
- ✅ Rollback tested

---

## 💾 PHASE 2: Storage & IAM (Days 8-11)

**Owner:** Lead Engineer
**Reviewer:** DevOps Lead
**Status:** ⏳ Pending

### 2.1 S3 Storage

- [ ] **2.1.1 Plan S3**
  - [ ] Run `terraform plan -target=module.aws_s3`
  - [ ] Review bucket configuration
  - [ ] Verify versioning & encryption enabled
  - [ ] Checkpoint: Plan reviewed ✓

- [ ] **2.1.2 Apply S3**
  - [ ] Run `terraform apply`
  - [ ] Verify buckets created: `aws s3 ls`
  - [ ] Check versioning: `aws s3api get-bucket-versioning`
  - [ ] Check encryption: `aws s3api get-bucket-encryption`
  - [ ] Checkpoint: S3 buckets created ✓

### 2.2 IAM Roles & IRSA

- [ ] **2.2.1 Plan IAM**
  - [ ] Run `terraform plan -target=module.aws_iam`
  - [ ] Review workload role configuration
  - [ ] Verify trust relationships
  - [ ] Checkpoint: Plan reviewed ✓

- [ ] **2.2.2 Apply IAM**
  - [ ] Run `terraform apply`
  - [ ] Get role ARN: `terraform output aws_iam_role_arn`
  - [ ] Verify trust policy: `aws iam get-role`
  - [ ] Checkpoint: IAM roles created ✓

### 2.3 ECR Container Registry

- [ ] **2.3.1 Plan ECR**
  - [ ] Run `terraform plan -target=module.aws_ecr`
  - [ ] Review repository configuration
  - [ ] Verify lifecycle policies
  - [ ] Checkpoint: Plan reviewed ✓

- [ ] **2.3.2 Apply ECR**
  - [ ] Run `terraform apply`
  - [ ] List repositories: `aws ecr describe-repositories`
  - [ ] Test login: `aws ecr get-login-password | docker login`
  - [ ] Checkpoint: ECR repositories created ✓

### 2.4 Cognito Setup

- [ ] **2.4.1 Plan Cognito**
  - [ ] Run `terraform plan -target=module.aws_cognito`
  - [ ] Review user pool configuration
  - [ ] Review app client settings
  - [ ] Checkpoint: Plan reviewed ✓

- [ ] **2.4.2 Apply Cognito**
  - [ ] Run `terraform apply`
  - [ ] Get user pool ID: `terraform output aws_cognito_user_pool_id`
  - [ ] Get client ID: `terraform output aws_cognito_client_id`
  - [ ] Get issuer URL: `terraform output aws_cognito_issuer_url`
  - [ ] Save to .env file
  - [ ] Checkpoint: Cognito configured ✓

### 2.5 IAM Permission Testing

- [ ] **2.5.1 S3 Access Verification**
  - [ ] Check IAM policy: `aws iam get-role-policy`
  - [ ] Verify S3 permissions present
  - [ ] Checkpoint: S3 access ready ✓

- [ ] **2.5.2 ECR Access Verification**
  - [ ] Test ECR login
  - [ ] Push test image (optional): `docker push <test-image>`
  - [ ] Verify image in repository
  - [ ] Checkpoint: ECR access ready ✓

**Phase 2 Sign-Off:**
- ✅ S3 buckets created with versioning
- ✅ IAM roles configured with IRSA
- ✅ ECR repositories ready
- ✅ Cognito user pool configured
- ✅ Permissions verified

---

## 🎮 PHASE 3: Kubernetes & Application (Days 12-15)

**Owner:** Lead Engineer
**Reviewer:** DevOps Lead
**Status:** ⏳ Pending

### 3.1 CSI Drivers

- [ ] **3.1.1 Plan CSI**
  - [ ] Run `terraform plan -target=module.csi_drivers`
  - [ ] Review S3 CSI driver config
  - [ ] Verify EBS CSI driver
  - [ ] Checkpoint: Plan reviewed ✓

- [ ] **3.1.2 Apply CSI**
  - [ ] Run `terraform apply`
  - [ ] Verify pods: `kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-mountpoint-s3-csi-driver`
  - [ ] Check CSI drivers: `kubectl get csidriver`
  - [ ] Checkpoint: CSI drivers installed ✓

### 3.2 cert-manager & TLS

- [ ] **3.2.1 Plan cert-manager**
  - [ ] Run `terraform plan -target=module.cert_manager`
  - [ ] Review ClusterIssuer configuration
  - [ ] Checkpoint: Plan reviewed ✓

- [ ] **3.2.2 Apply cert-manager**
  - [ ] Run `terraform apply`
  - [ ] Verify pods: `kubectl get pods -n cert-manager`
  - [ ] Check ClusterIssuer: `kubectl get clusterissuer`
  - [ ] Checkpoint: cert-manager deployed ✓

### 3.3 AWS Load Balancer Controller

- [ ] **3.3.1 Plan ALB Controller**
  - [ ] Run `terraform plan -target=module.aws_load_balancer_controller`
  - [ ] Review service account configuration
  - [ ] Verify IRSA role attachment
  - [ ] Checkpoint: Plan reviewed ✓

- [ ] **3.3.2 Apply ALB Controller**
  - [ ] Run `terraform apply`
  - [ ] Verify pods: `kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller`
  - [ ] Check service account: `kubectl get sa -n kube-system aws-load-balancer-controller -o yaml | grep role-arn`
  - [ ] Checkpoint: ALB controller deployed ✓

### 3.4 Application Deployment

- [ ] **3.4.1 Plan Helm**
  - [ ] Run `terraform plan -target=module.helm_deployment`
  - [ ] Review backend/frontend configuration
  - [ ] Verify ingress settings
  - [ ] Checkpoint: Plan reviewed ✓

- [ ] **3.4.2 Apply Helm**
  - [ ] Run `terraform apply`
  - [ ] Verify deployments: `kubectl get deployments -n cmbcluster`
  - [ ] Check pods: `kubectl get pods -n cmbcluster`
  - [ ] Check services: `kubectl get svc -n cmbcluster`
  - [ ] Wait for LoadBalancer IP: `kubectl get svc -n cmbcluster -w`
  - [ ] Checkpoint: Application deployed ✓

### 3.5 Application Verification

- [ ] **3.5.1 API Health**
  - [ ] Get ALB DNS: `kubectl get svc -n cmbcluster`
  - [ ] Test endpoint: `curl http://<ALB-DNS>/health`
  - [ ] Expected: 200 OK
  - [ ] Checkpoint: API accessible ✓

- [ ] **3.5.2 Pod Readiness**
  - [ ] Check logs: `kubectl logs -n cmbcluster deployment/cmbcluster-backend`
  - [ ] Check environment: `kubectl exec ... -- env | grep CLOUD_PROVIDER`
  - [ ] Verify S3 CSI driver mounts (if used)
  - [ ] Checkpoint: Pods ready ✓

- [ ] **3.5.3 TLS Certificates**
  - [ ] Check certificates: `kubectl get certificate -n cmbcluster`
  - [ ] Verify ready: `kubectl describe certificate -n cmbcluster`
  - [ ] Expected: Ready = True
  - [ ] Checkpoint: TLS certificates issued ✓

**Phase 3 Sign-Off:**
- ✅ All Kubernetes controllers deployed
- ✅ Application running
- ✅ LoadBalancer accessible
- ✅ TLS certificates configured
- ✅ API responding correctly

---

## 🌍 PHASE 4: GCP Parity & Validation (Days 16-19)

**Owner:** Lead Engineer + GCP Specialist
**Reviewer:** DevOps Lead
**Status:** ⏳ Pending

### 4.1 GCP Infrastructure

- [ ] **4.1.1 Create GCP Variables**
  - [ ] Copy dev.tfvars to gcp.local.tfvars
  - [ ] Set cloud_provider = "gcp"
  - [ ] Set GCP project ID and region
  - [ ] Checkpoint: Variables ready ✓

- [ ] **4.1.2 Plan GCP**
  - [ ] Run `terraform plan -var-file=gcp.local.tfvars`
  - [ ] Review GCP resources
  - [ ] Verify GKE cluster configuration
  - [ ] Checkpoint: Plan reviewed ✓

- [ ] **4.1.3 Apply GCP**
  - [ ] Run `terraform apply -var-file=gcp.local.tfvars`
  - [ ] Wait for GKE cluster (~20 min)
  - [ ] Verify GKE: `gcloud container clusters list`
  - [ ] Configure kubectl for GCP
  - [ ] Checkpoint: GCP cluster created ✓

### 4.2 GCP Storage & IAM

- [ ] **4.2.1 Plan GCS**
  - [ ] Run `terraform plan -target=module.gcp_storage -var-file=gcp.local.tfvars`
  - [ ] Review bucket configuration
  - [ ] Checkpoint: Plan reviewed ✓

- [ ] **4.2.2 Apply GCS**
  - [ ] Run `terraform apply`
  - [ ] Verify buckets: `gsutil ls -p <project-id>`
  - [ ] Checkpoint: GCS buckets created ✓

- [ ] **4.2.3 Plan Workload Identity**
  - [ ] Run `terraform plan -target=module.gcp_iam -var-file=gcp.local.tfvars`
  - [ ] Review service account configuration
  - [ ] Checkpoint: Plan reviewed ✓

- [ ] **4.2.4 Apply Workload Identity**
  - [ ] Run `terraform apply`
  - [ ] Verify service accounts: `gcloud iam service-accounts list`
  - [ ] Checkpoint: Workload Identity configured ✓

### 4.3 GCP Application Deployment

- [ ] **4.3.1 Deploy Kubernetes Components**
  - [ ] Plan & apply Kubernetes modules
  - [ ] Verify namespace, CSI, cert-manager
  - [ ] Checkpoint: Components deployed ✓

- [ ] **4.3.2 Deploy Application**
  - [ ] Plan & apply Helm deployment
  - [ ] Verify pods running
  - [ ] Check ingress
  - [ ] Checkpoint: Application deployed ✓

### 4.4 Comparison Testing

- [ ] **4.4.1 AWS vs GCP Comparison**
  - [ ] Switch kubectl contexts
  - [ ] Verify both clusters accessible
  - [ ] Compare API endpoints
  - [ ] Test both clusters simultaneously
  - [ ] Checkpoint: Both clouds working ✓

- [ ] **4.4.2 Feature Parity**
  - [ ] Verify identical pod behavior
  - [ ] Compare storage configurations
  - [ ] Test IAM bindings (Workload Identity vs IRSA)
  - [ ] Verify TLS on both
  - [ ] Checkpoint: Full parity confirmed ✓

**Phase 4 Sign-Off:**
- ✅ GCP infrastructure matches AWS
- ✅ GKE cluster operational
- ✅ Workload Identity configured
- ✅ GCS buckets ready
- ✅ Application deployed on both clouds
- ✅ Feature parity verified

---

## ✅ PHASE 5: Cutover & Deprecation (Days 20-21)

**Owner:** Lead Engineer + DevOps Lead
**Reviewer:** Engineering Manager
**Status:** ⏳ Pending

### 5.1 Parallel Verification

- [ ] **5.1.1 Health Check Both Systems**
  - [ ] Verify shell scripts running (if keeping)
  - [ ] Verify Terraform infrastructure healthy
  - [ ] Run parallel load tests
  - [ ] Compare performance metrics
  - [ ] Checkpoint: Both systems healthy ✓

### 5.2 Migrate to Remote State

- [ ] **5.2.1 Enable S3 Backend**
  - [ ] Uncomment backend in terraform/backend.tf
  - [ ] Run `terraform init`
  - [ ] Confirm migration when prompted
  - [ ] Checkpoint: State migrated to S3 ✓

- [ ] **5.2.2 Verify Remote State**
  - [ ] Confirm file in S3: `aws s3 ls s3://cmbcluster-terraform-state-aws/`
  - [ ] Backup local state: `terraform state pull > state-backup.json`
  - [ ] Verify DynamoDB locks working
  - [ ] Checkpoint: Remote state verified ✓

### 5.3 Update Documentation & CI/CD

- [ ] **5.3.1 Deprecate Shell Scripts**
  - [ ] Add DEPRECATED.md header
  - [ ] Archive to legacy/ directory
  - [ ] Update README
  - [ ] Checkpoint: Shell scripts deprecated ✓

- [ ] **5.3.2 Create CI/CD Pipeline**
  - [ ] Create .github/workflows/terraform.yml
  - [ ] Configure Terraform plan on PR
  - [ ] Configure Terraform apply on main push
  - [ ] Test workflow
  - [ ] Checkpoint: CI/CD configured ✓

### 5.4 Team Training

- [ ] **5.4.1 Workshop**
  - [ ] Present Terraform workflow
  - [ ] Hands-on practice (each engineer)
  - [ ] Rollback procedure walkthrough
  - [ ] Q&A session
  - [ ] Checkpoint: Team trained ✓

- [ ] **5.4.2 Documentation Handoff**
  - [ ] Provide all guides
  - [ ] Setup team wiki/docs
  - [ ] Record video tutorials (optional)
  - [ ] Create runbooks
  - [ ] Checkpoint: Documentation handed off ✓

### 5.5 Final Validation

- [ ] **5.5.1 Acceptance Criteria**
  - [ ] ✅ Infrastructure deployed via Terraform
  - [ ] ✅ State in S3/GCS
  - [ ] ✅ Both AWS and GCP working
  - [ ] ✅ CI/CD pipeline functional
  - [ ] ✅ Team trained
  - [ ] ✅ Documentation complete
  - [ ] ✅ Rollback tested

- [ ] **5.5.2 Sign-Offs**
  - [ ] Engineer: "Code ready for production"
  - [ ] DevOps Lead: "Infrastructure production-ready"
  - [ ] Engineering Manager: "Team confident"
  - [ ] CTO: "Approved for deployment"

- [ ] **5.5.3 Final Commit**
  - [ ] Merge feature branch to main
  - [ ] Tag release: `terraform-v1.0`
  - [ ] Create GitHub release notes
  - [ ] Checkpoint: Cutover complete ✓

**Phase 5 Sign-Off:**
- ✅ Shell scripts deprecated
- ✅ Terraform managing all infrastructure
- ✅ Remote state configured
- ✅ CI/CD pipeline working
- ✅ Team trained and confident
- ✅ Production deployment approved

---

## 🎯 Success Metrics

### Deployment Success
- [ ] All 6 phases completed on schedule
- [ ] Zero production incidents during cutover
- [ ] All acceptance criteria met
- [ ] All sign-offs obtained

### Code Quality
- [ ] Terraform code passes validation
- [ ] No hardcoded credentials
- [ ] All resources properly tagged
- [ ] State file backed up

### Team Success
- [ ] Team confident with Terraform
- [ ] Documentation complete
- [ ] All procedures documented
- [ ] Emergency procedures tested

### Production Readiness
- [ ] Infrastructure cost optimized
- [ ] Monitoring configured
- [ ] Alerting operational
- [ ] Disaster recovery tested

---

## 📞 Support Matrix

| Issue | Phase | Contact | Action |
|-------|-------|---------|--------|
| Terraform syntax error | Any | Lead Engineer | Fix code, replan |
| AWS API error | 1-3, 5 | AWS Specialist | Check API limits, retry |
| GCP API error | 4 | GCP Specialist | Check project perms, retry |
| Team training questions | 0, 5 | DevOps Lead | Schedule workshop |
| Production blockers | Any | Engineering Manager | Escalate, activate rollback |

---

## 🚀 Ready to Start?

✅ **Checklist before Phase 0 kickoff:**
- [ ] All team members read TERRAFORM_IMPLEMENTATION_GUIDE.md
- [ ] AWS credentials configured
- [ ] GCP credentials configured
- [ ] All tools installed
- [ ] Schedule kickoff meeting

**Let's go!** 🚀

---

**Prepared by:** Terraform Planning
**Status:** ✅ **READY FOR PHASE 0 KICKOFF**
**Next Step:** Schedule Phase 0 start date

