terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }

  # Uncomment for remote state management
  # backend "s3" {
  #   bucket         = "cmbcluster-terraform-state"
  #   key            = "terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }

  # For GCP:
  # backend "gcs" {
  #   bucket = "cmbcluster-terraform-state"
  #   prefix = "terraform/state"
  # }
}

# AWS Provider Configuration
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn = var.aws_assume_role_arn != "" ? var.aws_assume_role_arn : null
  }

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "Terraform"
      CreatedAt   = timestamp()
    }
  }
}

# GCP Provider Configuration
provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region

  # Use service account if provided
  # credentials = file(var.gcp_credentials_file)
}

# Kubernetes Provider (AWS EKS)
provider "kubernetes" {
  count = var.cloud_provider == "aws" ? 1 : 0

  host                   = module.aws_eks[0].cluster_endpoint
  cluster_ca_certificate = base64decode(module.aws_eks[0].cluster_ca_certificate)
  token                  = data.aws_eks_auth.cluster[0].token

  skip_credentials_validation = false
  skip_provider_registration  = false
}

# Kubernetes Provider (GCP GKE)
provider "kubernetes" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  host                   = "https://${module.gcp_gke[0].kubernetes_cluster_host}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(module.gcp_gke[0].kubernetes_cluster_ca_certificate)
}

# Helm Provider (AWS)
provider "helm" {
  count = var.cloud_provider == "aws" ? 1 : 0

  kubernetes {
    host                   = module.aws_eks[0].cluster_endpoint
    cluster_ca_certificate = base64decode(module.aws_eks[0].cluster_ca_certificate)
    token                  = data.aws_eks_auth.cluster[0].token
  }
}

# Helm Provider (GCP)
provider "helm" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  kubernetes {
    host                   = "https://${module.gcp_gke[0].kubernetes_cluster_host}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(module.gcp_gke[0].kubernetes_cluster_ca_certificate)
  }
}

# Get EKS authentication token
data "aws_eks_auth" "cluster" {
  count = var.cloud_provider == "aws" ? 1 : 0
  name  = module.aws_eks[0].cluster_name
}

# Get GCP credentials
data "google_client_config" "default" {}

# ============================================================================
# AWS INFRASTRUCTURE
# ============================================================================

module "aws_vpc" {
  count = var.cloud_provider == "aws" ? 1 : 0

  source = "./modules/aws/vpc"

  cluster_name = var.cluster_name
  region       = var.aws_region
  vpc_cidr     = var.aws_vpc_cidr

  public_subnets  = var.aws_public_subnets
  private_subnets = var.aws_private_subnets
  availability_zones = var.aws_availability_zones

  tags = local.common_tags
}

module "aws_eks" {
  count = var.cloud_provider == "aws" ? 1 : 0

  source = "./modules/aws/eks"

  cluster_name    = var.cluster_name
  vpc_id          = module.aws_vpc[0].vpc_id
  subnet_ids      = module.aws_vpc[0].private_subnet_ids

  kubernetes_version = var.kubernetes_version
  node_group_min_size = var.aws_node_group_min_size
  node_group_max_size = var.aws_node_group_max_size
  node_instance_type  = var.aws_node_instance_type

  tags = local.common_tags

  depends_on = [module.aws_vpc]
}

module "aws_ecr" {
  count = var.cloud_provider == "aws" ? 1 : 0

  source = "./modules/aws/ecr"

  cluster_name = var.cluster_name
  repositories = ["backend", "frontend"]

  tags = local.common_tags
}

module "aws_s3" {
  count = var.cloud_provider == "aws" ? 1 : 0

  source = "./modules/aws/s3"

  cluster_name     = var.cluster_name
  aws_account_id   = data.aws_caller_identity.current.account_id
  versioning_enabled = true
  enable_encryption = true

  tags = local.common_tags
}

module "aws_iam" {
  count = var.cloud_provider == "aws" ? 1 : 0

  source = "./modules/aws/iam"

  cluster_name    = var.cluster_name
  cluster_arn     = module.aws_eks[0].cluster_arn
  oidc_provider   = module.aws_eks[0].oidc_provider_arn

  s3_bucket_arns  = module.aws_s3[0].bucket_arns
  ecr_registry_arn = module.aws_ecr[0].registry_arn

  tags = local.common_tags
}

module "aws_cognito" {
  count = var.cloud_provider == "aws" && var.enable_cognito ? 1 : 0

  source = "./modules/aws/cognito"

  user_pool_name           = "${var.cluster_name}-users"
  app_client_name          = "${var.cluster_name}-app"
  callback_urls            = var.cognito_callback_urls
  allowed_logout_urls      = var.cognito_logout_urls
  domain_prefix            = "${var.cluster_name}-auth"

  tags = local.common_tags
}

# ============================================================================
# GCP INFRASTRUCTURE
# ============================================================================

module "gcp_gke" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  source = "./modules/gcp/gke"

  project_id       = var.gcp_project_id
  region           = var.gcp_region
  cluster_name     = var.cluster_name

  network_name     = module.gcp_network[0].network_name
  subnet_names     = module.gcp_network[0].subnet_names

  kubernetes_version      = var.kubernetes_version
  node_pool_initial_size  = var.gcp_node_pool_initial_size
  node_pool_min_size      = var.gcp_node_pool_min_size
  node_pool_max_size      = var.gcp_node_pool_max_size
  node_machine_type       = var.gcp_node_machine_type

  tags = local.common_tags

  depends_on = [module.gcp_network]
}

module "gcp_network" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  source = "./modules/gcp/network"

  project_id = var.gcp_project_id
  region     = var.gcp_region

  network_name = "${var.cluster_name}-network"
  subnet_cidrs = var.gcp_subnet_cidrs

  tags = local.common_tags
}

module "gcp_storage" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  source = "./modules/gcp/storage"

  project_id   = var.gcp_project_id
  cluster_name = var.cluster_name

  versioning_enabled = true
  enable_encryption  = true

  tags = local.common_tags
}

module "gcp_artifact_registry" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  source = "./modules/gcp/artifact-registry"

  project_id   = var.gcp_project_id
  region       = var.gcp_region
  cluster_name = var.cluster_name

  repositories = ["backend", "frontend"]
}

module "gcp_iam" {
  count = var.cloud_provider == "gcp" ? 1 : 0

  source = "./modules/gcp/iam"

  project_id       = var.gcp_project_id
  cluster_name     = var.cluster_name
  cluster_workload_identity_pool = module.gcp_gke[0].workload_identity_pool

  tags = local.common_tags
}

# ============================================================================
# KUBERNETES INFRASTRUCTURE (Common)
# ============================================================================

module "kubernetes_namespaces" {
  count = var.cloud_provider != "" ? 1 : 0

  source = "./modules/kubernetes/namespaces"

  namespace_name = var.kubernetes_namespace

  depends_on = [
    module.aws_eks,
    module.gcp_gke
  ]
}

module "csi_drivers" {
  count = var.cloud_provider != "" ? 1 : 0

  source = "./modules/kubernetes/csi-drivers"

  cloud_provider = var.cloud_provider
  namespace      = var.kubernetes_namespace

  # AWS S3 CSI Driver
  aws_s3_csi_version = var.aws_s3_csi_driver_version

  # GCP GCS FUSE CSI Driver
  gcp_gcs_fuse_version = var.gcp_gcs_fuse_csi_driver_version

  depends_on = [module.kubernetes_namespaces]
}

module "cert_manager" {
  count = var.cloud_provider != "" ? 1 : 0

  source = "./modules/kubernetes/cert-manager"

  namespace       = var.kubernetes_namespace
  letsencrypt_email = var.letsencrypt_email
  use_staging     = !var.production_environment

  depends_on = [module.kubernetes_namespaces]
}

module "aws_load_balancer_controller" {
  count = var.cloud_provider == "aws" ? 1 : 0

  source = "./modules/kubernetes/aws-load-balancer-controller"

  cluster_name     = var.cluster_name
  cluster_arn      = module.aws_eks[0].cluster_arn
  namespace        = var.kubernetes_namespace
  oidc_provider_arn = module.aws_eks[0].oidc_provider_arn

  service_account_role_arn = module.aws_iam[0].alb_controller_role_arn

  depends_on = [
    module.kubernetes_namespaces,
    module.aws_iam
  ]
}

# ============================================================================
# HELM DEPLOYMENTS
# ============================================================================

module "helm_deployment" {
  count = var.cloud_provider != "" && var.deploy_application ? 1 : 0

  source = "./modules/kubernetes/helm"

  cluster_name    = var.cluster_name
  namespace       = var.kubernetes_namespace
  cloud_provider  = var.cloud_provider

  # Backend configuration
  backend_image_uri = var.backend_image_uri
  backend_replicas  = var.backend_replicas

  # Frontend configuration
  frontend_image_uri = var.frontend_image_uri
  frontend_replicas  = var.frontend_replicas

  # Cloud-specific configuration
  gcp_project_id      = var.gcp_project_id
  aws_account_id      = data.aws_caller_identity.current.account_id
  aws_region          = var.aws_region

  # Authentication
  auth_provider          = var.auth_provider
  google_client_id       = var.google_client_id
  google_client_secret   = var.google_client_secret
  cognito_user_pool_id   = try(module.aws_cognito[0].user_pool_id, "")
  cognito_client_id      = try(module.aws_cognito[0].client_id, "")
  cognito_client_secret  = try(module.aws_cognito[0].client_secret, "")
  cognito_issuer         = try(module.aws_cognito[0].issuer_url, "")

  # Secrets
  secret_key = var.secret_key
  nextauth_secret = var.nextauth_secret

  # Domain configuration
  domain              = var.domain
  api_url             = var.api_url
  frontend_url        = var.frontend_url
  tls_enabled         = var.tls_enabled
  cluster_issuer      = var.cluster_issuer

  depends_on = [
    module.kubernetes_namespaces,
    module.csi_drivers,
    module.cert_manager,
    module.aws_load_balancer_controller
  ]
}

# ============================================================================
# DATA SOURCES
# ============================================================================

data "aws_caller_identity" "current" {}

# ============================================================================
# LOCAL VALUES
# ============================================================================

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
