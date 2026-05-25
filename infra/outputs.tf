output "bucket_name" {
  value = google_storage_bucket.market_data.name
}

output "artifact_registry_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repo}"
}

output "showresults_url" {
  value = google_cloud_run_v2_service.showresults.uri
}

