variable "project_id" {
  type        = string
  description = "The GCP Project ID"
}

variable "region" {
  type        = string
  description = "The GCP Region"
  default     = "europe-west1"
}

variable "bucket_name" {
  type        = string
  description = "The name of the GCS bucket to store market data state"
}

variable "artifact_registry_repo" {
  type        = string
  description = "The name of the Artifact Registry repository for Docker images"
  default     = "trading-regime-repo"
}
