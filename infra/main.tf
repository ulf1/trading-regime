# GCS Bucket
resource "google_storage_bucket" "market_data" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = false
  uniform_bucket_level_access = true
}

# Artifact Registry
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.artifact_registry_repo
  description   = "Docker repository for Trading Regime Cloud Run Jobs"
  format        = "DOCKER"
}

# Service Account
resource "google_service_account" "job_sa" {
  account_id   = "trading-regime-job-sa"
  display_name = "Trading Regime Cloud Run Job Service Account"
}

resource "google_storage_bucket_iam_member" "sa_bucket_access" {
  bucket = google_storage_bucket.market_data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.job_sa.email}"
}

resource "google_project_iam_member" "sa_cloudrun_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.job_sa.email}"
}

# 1. Data Sync (Daily)
resource "google_cloud_run_v2_job" "datasync" {
  name     = "datasync-job"
  location = var.region

  template {
    template {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repo}/datasync:latest"
        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.market_data.name
        }
        resources {
          limits = {
            memory = "2Gi"
            cpu    = "1"
          }
        }
      }
      service_account = google_service_account.job_sa.email
    }
  }
}

resource "google_cloud_scheduler_job" "datasync_schedule" {
  name             = "datasync-schedule"
  description      = "Trigger Data Sync Job Daily"
  schedule         = "0 1 * * *"
  time_zone        = "CET"
  region           = var.region

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/datasync-job:run"

    oauth_token {
      service_account_email = google_service_account.job_sa.email
    }
  }
}

# 2. Ticker Checker (Weekly Sat 19:00 CET)
resource "google_cloud_run_v2_job" "tickerchecker" {
  name     = "tickerchecker-job"
  location = var.region

  template {
    template {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repo}/tickerchecker:latest"
        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.market_data.name
        }
        resources {
          limits = {
            memory = "2Gi"
            cpu    = "1"
          }
        }
      }
      service_account = google_service_account.job_sa.email
    }
  }
}

resource "google_cloud_scheduler_job" "tickerchecker_schedule" {
  name             = "tickerchecker-schedule"
  description      = "Trigger Ticker Checker Weekly on Sat 19:00 CET"
  schedule         = "0 19 * * 6"
  time_zone        = "CET"
  region           = var.region

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/tickerchecker-job:run"

    oauth_token {
      service_account_email = google_service_account.job_sa.email
    }
  }
}

# 3. Find Ticker (Daily 22:00 CET)
resource "google_cloud_run_v2_job" "findticker" {
  name     = "findticker-job"
  location = var.region

  template {
    template {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repo}/findticker:latest"
        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.market_data.name
        }
        resources {
          limits = {
            memory = "2Gi"
            cpu    = "1"
          }
        }
      }
      service_account = google_service_account.job_sa.email
    }
  }
}

resource "google_cloud_scheduler_job" "findticker_schedule" {
  name             = "findticker-schedule"
  description      = "Trigger Find Ticker Daily 22:00 CET"
  schedule         = "0 22 * * *"
  time_zone        = "CET"
  region           = var.region

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/findticker-job:run"

    oauth_token {
      service_account_email = google_service_account.job_sa.email
    }
  }
}

# 4. Initial Downloader (Sun 15:00 CET)
resource "google_cloud_run_v2_job" "initialdownloader" {
  name     = "initialdownloader-job"
  location = var.region

  template {
    template {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repo}/initialdownloader:latest"
        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.market_data.name
        }
        resources {
          limits = {
            memory = "2Gi"
            cpu    = "1"
          }
        }
      }
      service_account = google_service_account.job_sa.email
    }
  }
}

resource "google_cloud_scheduler_job" "initialdownloader_schedule" {
  name             = "initialdownloader-schedule"
  description      = "Trigger Initial Downloader Weekly on Sun 15:00 CET"
  schedule         = "0 15 * * 0"
  time_zone        = "CET"
  region           = var.region

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/initialdownloader-job:run"

    oauth_token {
      service_account_email = google_service_account.job_sa.email
    }
  }
}
