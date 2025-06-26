output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.jupyterhub_cluster.name
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.jupyterhub_cluster.endpoint
  sensitive   = true
}

output "storage_bucket" {
  description = "Storage bucket name"
  value       = google_storage_bucket.jupyterhub_storage.name
}
