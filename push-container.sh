# Authenticate Docker to GCP Artifact Registry
gcloud auth configure-docker europe-west1-docker.pkg.dev

# Define variables
PROJECT_ID="trading-systems-497317"
REGION="europe-west1"
REPO="trading-regime-repo"

# Build & Push datasync
docker build --no-cache -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/datasync:latest ./datasync
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/datasync:latest

# Build & Push tickerchecker
docker build --no-cache -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/tickerchecker:latest ./tickerchecker
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/tickerchecker:latest

# Build & Push findticker
docker build --no-cache -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/findticker:latest ./findticker
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/findticker:latest

# Build & Push initialdownloader
docker build --no-cache -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/initialdownloader:latest ./initialdownloader
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/initialdownloader:latest

# Build & Push trainer
docker build --no-cache -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/trainer:latest ./trainer
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/trainer:latest

# Build & Push showresults
docker build --no-cache -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/showresults:latest ./showresults
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/showresults:latest


