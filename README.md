# Trading Regime Data Pipelines

This project implements a set of daily and weekly data synchronization, discovery, and backfilling pipelines for market data (Yahoo Finance), running as GCP Cloud Run Jobs triggered by Cloud Scheduler.

## Project Structure

The project is structured as a mono-repo containing the following main components:

*   **`datasync/`**: Daily synchronization of the latest 10 days of market data for the active list of tickers.
*   **`tickerchecker/`**: Weekly health checker that flags, logs, and cleans up dead or stale tickers.
*   **`findticker/`**: Daily ticker discovery job that scrapes Yahoo Finance's most-active list to discover new active stocks.
*   **`initialdownloader/`**: Scheduled job that ensures all active tickers have at least 2,000 historical price points.
*   **`infra/`**: Infrastructure-as-Code using Terraform to provision GCP resources (GCS Buckets, Cloud Run Jobs, Cloud Scheduler, Artifact Registry).
*   **`specs/`**: Technical specification documents for all pipelines.

---

## Next Steps for Deployment and Execution

Follow these steps to run, validate, and deploy the trading regime data pipelines:

### 1. Run Unit Tests Locally

Ensure the application code for each pipeline works correctly using `uv`:

```bash
# Data Sync Tests
cd datasync && uv run pytest tests/

# Ticker Checker Tests
cd ../tickerchecker && uv run pytest tests/

# Find Ticker Tests
cd ../findticker && uv run pytest tests/

# Initial Downloader Tests
cd ../initialdownloader && uv run pytest tests/
```

### 2. Configure Terraform Variables

Before deploying the infrastructure, define the required variables in a `terraform.tfvars` file under the `infra/` directory, or pass them during apply.

Create `infra/terraform.tfvars`:
```hcl
project_id             = "your-gcp-project-id"
region                 = "europe-west1"
bucket_name            = "your-globally-unique-gcs-bucket-name"
artifact_registry_repo = "trading-regime-repo"
```

### 3. Deploy the GCP Infrastructure

Initialize and apply the Terraform configuration to provision the GCS bucket, Artifact Registry repository, Service Accounts, Cloud Run Jobs, and Cloud Schedulers.

```bash
cd infra
terraform init
terraform apply
```

### 4. Build and Push Container Images

Once the Artifact Registry is created, configure Docker credentials and build/push the container images for each of the four pipelines:

```bash
# Authenticate Docker to GCP Artifact Registry
gcloud auth configure-docker europe-west1-docker.pkg.dev

# Define variables
PROJECT_ID="your-gcp-project-id"
REGION="europe-west1"
REPO="trading-regime-repo"

# Build & Push datasync
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/datasync:latest ./datasync
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/datasync:latest

# Build & Push tickerchecker
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/tickerchecker:latest ./tickerchecker
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/tickerchecker:latest

# Build & Push findticker
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/findticker:latest ./findticker
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/findticker:latest

# Build & Push initialdownloader
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/initialdownloader:latest ./initialdownloader
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/initialdownloader:latest
```

### 5. Verify the Pipelines

Once images are pushed:
1. Go to the **Google Cloud Run** console.
2. Select any of the newly created jobs (e.g., `datasync-job`).
3. Click **Execute** to run the job manually and check the logs.
