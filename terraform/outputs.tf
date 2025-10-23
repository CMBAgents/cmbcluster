# ============================================================================
# AWS OUTPUTS
# ============================================================================

output "aws_eks_cluster_name" {
  description = "EKS cluster name"
  value       = try(module.aws_eks[0].cluster_name, null)
}

output "aws_eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = try(module.aws_eks[0].cluster_endpoint, null)
}

output "aws_eks_cluster_arn" {
  description = "EKS cluster ARN"
  value       = try(module.aws_eks[0].cluster_arn, null)
}

output "aws_ecr_registry_url" {
  description = "ECR registry URL"
  value       = try(module.aws_ecr[0].registry_url, null)
}

output "aws_ecr_repositories" {
  description = "ECR repository details"
  value       = try(module.aws_ecr[0].repositories, {})
}

output "aws_s3_bucket_names" {
  description = "S3 bucket names"
  value       = try(module.aws_s3[0].bucket_names, {})
}

output "aws_database_bucket" {
  description = "S3 database bucket name"
  value       = try(module.aws_s3[0].database_bucket_name, null)
}

output "aws_vpc_id" {
  description = "VPC ID"
  value       = try(module.aws_vpc[0].vpc_id, null)
}

output "aws_private_subnet_ids" {
  description = "Private subnet IDs"
  value       = try(module.aws_vpc[0].private_subnet_ids, [])
}

output "aws_cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = try(module.aws_cognito[0].user_pool_id, null)
}

output "aws_cognito_client_id" {
  description = "Cognito App Client ID"
  value       = try(module.aws_cognito[0].client_id, null)
  sensitive   = true
}

output "aws_cognito_client_secret" {
  description = "Cognito App Client Secret"
  value       = try(module.aws_cognito[0].client_secret, null)
  sensitive   = true
}

output "aws_cognito_issuer_url" {
  description = "Cognito Issuer URL"
  value       = try(module.aws_cognito[0].issuer_url, null)
}

output "aws_iam_role_arn" {
  description = "IAM role ARN for pod permissions"
  value       = try(module.aws_iam[0].workload_role_arn, null)
}

# ============================================================================
# GCP OUTPUTS
# ============================================================================

output "gcp_gke_cluster_name" {
  description = "GKE cluster name"
  value       = try(module.gcp_gke[0].cluster_name, null)
}

output "gcp_gke_endpoint" {
  description = "GKE cluster endpoint"
  value       = try(module.gcp_gke[0].kubernetes_cluster_host, null)
}

output "gcp_gke_region" {
  description = "GKE cluster region"
  value       = try(module.gcp_gke[0].region, null)
}

output "gcp_artifact_registry" {
  description = "Artifact Registry repository URL"
  value       = try(module.gcp_artifact_registry[0].repository_url, null)
}

output "gcp_gcs_buckets" {
  description = "GCS bucket names"
  value       = try(module.gcp_storage[0].bucket_names, {})
}

output "gcp_database_bucket" {
  description = "GCS database bucket name"
  value       = try(module.gcp_storage[0].database_bucket_name, null)
}

output "gcp_network_name" {
  description = "VPC network name"
  value       = try(module.gcp_network[0].network_name, null)
}

output "gcp_subnet_names" {
  description = "Subnet names"
  value       = try(module.gcp_network[0].subnet_names, [])
}

output "gcp_service_account_email" {
  description = "Workload Identity service account email"
  value       = try(module.gcp_iam[0].workload_sa_email, null)
}

# ============================================================================
# KUBERNETES OUTPUTS
# ============================================================================

output "kubernetes_namespace" {
  description = "Kubernetes namespace"
  value       = var.kubernetes_namespace
}

output "kubeconfig_command" {
  description = "Command to configure kubectl for the cluster"
  value       = var.cloud_provider == "aws" ? (
    "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.aws_eks[0].cluster_name}"
  ) : (
    "gcloud container clusters get-credentials ${module.gcp_gke[0].cluster_name} --region ${var.gcp_region} --project ${var.gcp_project_id}"
  )
  description = "Command to configure kubectl"
}

output "ingress_controller" {
  description = "Ingress controller type"
  value       = var.cloud_provider == "aws" ? "AWS Load Balancer Controller" : "GCP Load Balancer"
}

# ============================================================================
# APPLICATION OUTPUTS
# ============================================================================

output "application_backend_url" {
  description = "Backend API URL"
  value       = var.api_url
}

output "application_frontend_url" {
  description = "Frontend URL"
  value       = var.frontend_url
}

output "application_domain" {
  description = "Application domain"
  value       = var.domain
}

# ============================================================================
# CONFIGURATION FOR .ENV FILE
# ============================================================================

output "env_file_content" {
  description = "Content to add to .env file"
  value = var.cloud_provider == "aws" ? (
    templatefile("${path.module}/.env.template.aws", {
      cloud_provider      = "aws"
      aws_account_id      = data.aws_caller_identity.current.account_id
      aws_region          = var.aws_region
      eks_cluster_name    = module.aws_eks[0].cluster_name
      ecr_registry_url    = module.aws_ecr[0].registry_url
      s3_db_bucket        = module.aws_s3[0].database_bucket_name
      cognito_user_pool_id = try(module.aws_cognito[0].user_pool_id, "")
      cognito_client_id   = try(module.aws_cognito[0].client_id, "")
      cognito_issuer      = try(module.aws_cognito[0].issuer_url, "")
      domain              = var.domain
      api_url             = var.api_url
      frontend_url        = var.frontend_url
      auth_provider       = var.auth_provider
    })
  ) : (
    templatefile("${path.module}/.env.template.gcp", {
      cloud_provider      = "gcp"
      gcp_project_id      = var.gcp_project_id
      gcp_region          = var.gcp_region
      gke_cluster_name    = module.gcp_gke[0].cluster_name
      artifact_registry   = module.gcp_artifact_registry[0].repository_url
      gcs_db_bucket       = module.gcp_storage[0].database_bucket_name
      domain              = var.domain
      api_url             = var.api_url
      frontend_url        = var.frontend_url
      auth_provider       = var.auth_provider
    })
  )
  sensitive = true
}

# ============================================================================
# DEPLOYMENT SUMMARY
# ============================================================================

output "deployment_summary" {
  description = "Summary of deployed infrastructure"
  value = {
    cloud_provider  = var.cloud_provider
    cluster_name    = var.cluster_name
    region          = var.cloud_provider == "aws" ? var.aws_region : var.gcp_region
    environment     = var.environment
    kubernetes_namespace = var.kubernetes_namespace
    api_url         = var.api_url
    frontend_url    = var.frontend_url
    domain          = var.domain
    auth_provider   = var.auth_provider
  }
}

# ============================================================================
# NEXT STEPS
# ============================================================================

output "next_steps" {
  description = "Next steps after Terraform deployment"
  value = <<-EOT

    ✅ Infrastructure deployed successfully!

    Next steps:
    1. Configure kubectl:
       ${var.cloud_provider == "aws" ? "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.aws_eks[0].cluster_name}" : "gcloud container clusters get-credentials ${module.gcp_gke[0].cluster_name} --region ${var.gcp_region}"}

    2. Verify cluster access:
       kubectl get nodes
       kubectl get pods -n ${var.kubernetes_namespace}

    3. Build and push images:
       ${var.cloud_provider == "aws" ? "aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${module.aws_ecr[0].registry_url}" : "gcloud auth configure-docker"}

    4. Copy the .env content above to your .env file

    5. Deploy application:
       kubectl apply -f kubernetes/manifests/

    6. Monitor deployment:
       kubectl logs -f -n ${var.kubernetes_namespace} deployment/cmbcluster-backend
       kubectl logs -f -n ${var.kubernetes_namespace} deployment/cmbcluster-frontend

    7. Check ingress:
       kubectl get ingress -n ${var.kubernetes_namespace}
  EOT
}
