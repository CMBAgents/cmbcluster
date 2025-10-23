# ============================================================================
# CMBCluster Terraform Configuration - Development Environment
# ============================================================================

# Cloud Provider Selection
cloud_provider = "aws"  # or "gcp"
environment    = "dev"

# Cluster Configuration
cluster_name  = "cmbcluster-dev"
project_name  = "cmbcluster"

# Kubernetes Configuration
kubernetes_version = "1.28"
kubernetes_namespace = "cmbcluster"

# ============================================================================
# AWS Configuration (if using AWS)
# ============================================================================

aws_region              = "us-east-1"
aws_vpc_cidr            = "10.0.0.0/16"
aws_availability_zones  = ["us-east-1a", "us-east-1b", "us-east-1c"]

# Subnet Configuration
aws_public_subnets  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
aws_private_subnets = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]

# EKS Node Group Configuration (development)
aws_node_group_min_size    = 1
aws_node_group_max_size    = 3
aws_node_instance_type     = "t3.medium"

# AWS Services
aws_s3_csi_driver_version = "v1.5.0"
enable_cognito            = true

# Cognito URLs (set after creating ingress/load balancer)
cognito_callback_urls = [
  "http://localhost:3000/api/auth/callback/cognito",
  "https://cmbcluster-dev.example.com/api/auth/callback/cognito"
]
cognito_logout_urls = [
  "http://localhost:3000",
  "https://cmbcluster-dev.example.com"
]

# ============================================================================
# GCP Configuration (if using GCP)
# ============================================================================

# Uncomment and configure for GCP
# gcp_project_id = "your-gcp-project-id"
# gcp_region     = "us-central1"
#
# gcp_subnet_cidrs            = ["10.0.0.0/20", "10.16.0.0/20", "10.32.0.0/20"]
# gcp_node_pool_initial_size  = 2
# gcp_node_pool_min_size      = 1
# gcp_node_pool_max_size      = 5
# gcp_node_machine_type       = "e2-standard-2"

# ============================================================================
# Deployment Configuration
# ============================================================================

deploy_application = true

# Docker Images
backend_image_uri  = "docker.io/library/nginx:latest"  # Replace with your backend image
backend_replicas   = 1

frontend_image_uri = "docker.io/library/nginx:latest"  # Replace with your frontend image
frontend_replicas  = 1

# ============================================================================
# Domain & Networking
# ============================================================================

domain       = "cmbcluster-dev.local"
api_url      = "http://api.cmbcluster-dev.local"
frontend_url = "http://cmbcluster-dev.local"

tls_enabled   = false  # Development - use false for self-signed certs
cluster_issuer = "letsencrypt-staging"  # Use staging for development

# Let's Encrypt Email (for production)
letsencrypt_email = "your-email@example.com"

# ============================================================================
# Authentication
# ============================================================================

# Google OAuth (optional)
# auth_provider        = "google"
# google_client_id     = "your-google-client-id.apps.googleusercontent.com"
# google_client_secret = "your-google-client-secret"

# AWS Cognito (optional) - Will be auto-created by Terraform
auth_provider = "auto"

# ============================================================================
# Security
# ============================================================================

secret_key      = "dev-secret-key-minimum-32-characters-required-here"
nextauth_secret = "dev-nextauth-secret-minimum-32-characters-required-here"

production_environment = false

# ============================================================================
# Additional Tags
# ============================================================================

additional_tags = {
  Team        = "DevOps"
  CostCenter  = "Engineering"
  Compliance  = "Internal"
}
