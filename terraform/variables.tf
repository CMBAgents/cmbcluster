# ============================================================================
# GENERAL VARIABLES
# ============================================================================

variable "cloud_provider" {
  description = "Cloud provider to use: 'aws' or 'gcp'"
  type        = string
  validation {
    condition     = contains(["aws", "gcp"], var.cloud_provider)
    error_message = "cloud_provider must be 'aws' or 'gcp'"
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be 'dev', 'staging', or 'prod'"
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "cmbcluster"
}

variable "cluster_name" {
  description = "Kubernetes cluster name"
  type        = string
  default     = "cmbcluster"
}

variable "kubernetes_namespace" {
  description = "Kubernetes namespace for deployment"
  type        = string
  default     = "cmbcluster"
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

# ============================================================================
# AWS VARIABLES
# ============================================================================

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "aws_public_subnets" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "aws_private_subnets" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}

variable "aws_availability_zones" {
  description = "AWS availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "aws_node_group_min_size" {
  description = "Minimum size of EKS node group"
  type        = number
  default     = 1
}

variable "aws_node_group_max_size" {
  description = "Maximum size of EKS node group"
  type        = number
  default     = 3
}

variable "aws_node_instance_type" {
  description = "EC2 instance type for EKS nodes"
  type        = string
  default     = "t3.medium"
}

variable "aws_s3_csi_driver_version" {
  description = "Version of AWS S3 CSI Driver"
  type        = string
  default     = "v1.5.0"
}

variable "aws_assume_role_arn" {
  description = "ARN of role to assume for AWS operations (optional)"
  type        = string
  default     = ""
}

variable "enable_cognito" {
  description = "Whether to create AWS Cognito user pool"
  type        = bool
  default     = true
}

variable "cognito_callback_urls" {
  description = "Callback URLs for Cognito OAuth"
  type        = list(string)
  default     = []
}

variable "cognito_logout_urls" {
  description = "Logout URLs for Cognito"
  type        = list(string)
  default     = []
}

# ============================================================================
# GCP VARIABLES
# ============================================================================

variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
  default     = ""
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "gcp_subnet_cidrs" {
  description = "CIDR blocks for GCP subnets"
  type        = list(string)
  default     = ["10.0.0.0/20", "10.16.0.0/20", "10.32.0.0/20"]
}

variable "gcp_node_pool_initial_size" {
  description = "Initial size of GKE node pool"
  type        = number
  default     = 2
}

variable "gcp_node_pool_min_size" {
  description = "Minimum size of GKE node pool"
  type        = number
  default     = 1
}

variable "gcp_node_pool_max_size" {
  description = "Maximum size of GKE node pool"
  type        = number
  default     = 5
}

variable "gcp_node_machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-standard-2"
}

variable "gcp_gcs_fuse_csi_driver_version" {
  description = "Version of GCP GCS FUSE CSI Driver"
  type        = string
  default     = "v1.3.0"
}

# ============================================================================
# KUBERNETES & DEPLOYMENT VARIABLES
# ============================================================================

variable "deploy_application" {
  description = "Whether to deploy the application after infrastructure setup"
  type        = bool
  default     = true
}

variable "backend_image_uri" {
  description = "Docker image URI for backend"
  type        = string
  default     = "gcr.io/cmbcluster-dev/backend:latest"
}

variable "backend_replicas" {
  description = "Number of backend replicas"
  type        = number
  default     = 1
}

variable "frontend_image_uri" {
  description = "Docker image URI for frontend"
  type        = string
  default     = "gcr.io/cmbcluster-dev/frontend:latest"
}

variable "frontend_replicas" {
  description = "Number of frontend replicas"
  type        = number
  default     = 1
}

variable "letsencrypt_email" {
  description = "Email for Let's Encrypt certificate registration"
  type        = string
}

variable "production_environment" {
  description = "Whether this is a production environment"
  type        = bool
  default     = false
}

# ============================================================================
# DOMAIN & NETWORKING VARIABLES
# ============================================================================

variable "domain" {
  description = "Domain for application"
  type        = string
  default     = "cmbcluster.local"
}

variable "api_url" {
  description = "API URL"
  type        = string
  default     = "http://localhost:8000"
}

variable "frontend_url" {
  description = "Frontend URL"
  type        = string
  default     = "http://localhost:3000"
}

variable "tls_enabled" {
  description = "Whether to enable TLS"
  type        = bool
  default     = true
}

variable "cluster_issuer" {
  description = "ClusterIssuer name for cert-manager"
  type        = string
  default     = "letsencrypt-prod"
}

# ============================================================================
# AUTHENTICATION VARIABLES
# ============================================================================

variable "auth_provider" {
  description = "Authentication provider: 'auto', 'google', or 'cognito'"
  type        = string
  default     = "auto"
  validation {
    condition     = contains(["auto", "google", "cognito"], var.auth_provider)
    error_message = "auth_provider must be 'auto', 'google', or 'cognito'"
  }
}

variable "google_client_id" {
  description = "Google OAuth Client ID"
  type        = string
  default     = ""
  sensitive   = false
}

variable "google_client_secret" {
  description = "Google OAuth Client Secret"
  type        = string
  default     = ""
  sensitive   = true
}

# ============================================================================
# SECURITY VARIABLES
# ============================================================================

variable "secret_key" {
  description = "Backend secret key (min 32 characters)"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.secret_key) >= 32
    error_message = "secret_key must be at least 32 characters"
  }
}

variable "nextauth_secret" {
  description = "NextAuth secret key"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.nextauth_secret) >= 32
    error_message = "nextauth_secret must be at least 32 characters"
  }
}

# ============================================================================
# TAGS & LABELS
# ============================================================================

variable "additional_tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}
