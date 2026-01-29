#!/bin/bash
set -e

# Get project ID
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"

echo "Setting up ML Cloud Run Jobs for project: $PROJECT_ID"

# Build and push ML Docker image
echo "Building and pushing ML Docker image..."
cd ml
gcloud builds submit --config=cloudbuild.yaml
cd ..

# Get the latest image
ML_IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/shopsmart/ml:latest"

echo "Creating Cloud Run Jobs..."

# Create Data Loader Job
echo "Creating ml-data-loader job..."
gcloud run jobs create ml-data-loader \
  --image=$ML_IMAGE \
  --region=$REGION \
  --add-cloudsql-instances=$PROJECT_ID:$REGION:shopsmart-db \
  --vpc-connector=shopsmart-connector \
  --set-secrets=DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest \
  --cpu=1 \
  --memory=1Gi \
  --max-retries=1 \
  --task-timeout=30m \
  --service-account=shopsmart-ml@$PROJECT_ID.iam.gserviceaccount.com \
  --command=python,-m,data.seed.synthetic_generator \
  2>/dev/null || echo "ml-data-loader already exists, updating..."

if [ $? -ne 0 ]; then
  gcloud run jobs update ml-data-loader \
    --image=$ML_IMAGE \
    --region=$REGION
fi

# Create Trending Pipeline Job
echo "Creating ml-trending job..."
gcloud run jobs create ml-trending \
  --image=$ML_IMAGE \
  --region=$REGION \
  --add-cloudsql-instances=$PROJECT_ID:$REGION:shopsmart-db \
  --vpc-connector=shopsmart-connector \
  --set-secrets=DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest \
  --cpu=1 \
  --memory=512Mi \
  --max-retries=2 \
  --task-timeout=30m \
  --service-account=shopsmart-ml@$PROJECT_ID.iam.gserviceaccount.com \
  --command=python,-m,pipelines.trending_pipeline \
  2>/dev/null || echo "ml-trending already exists, updating..."

if [ $? -ne 0 ]; then
  gcloud run jobs update ml-trending \
    --image=$ML_IMAGE \
    --region=$REGION
fi

# Create Similarity Pipeline Job
echo "Creating ml-similarity job..."
gcloud run jobs create ml-similarity \
  --image=$ML_IMAGE \
  --region=$REGION \
  --add-cloudsql-instances=$PROJECT_ID:$REGION:shopsmart-db \
  --vpc-connector=shopsmart-connector \
  --set-secrets=DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest \
  --cpu=2 \
  --memory=4Gi \
  --max-retries=2 \
  --task-timeout=2h \
  --service-account=shopsmart-ml@$PROJECT_ID.iam.gserviceaccount.com \
  --command=python,-m,pipelines.similarity_pipeline \
  2>/dev/null || echo "ml-similarity already exists, updating..."

if [ $? -ne 0 ]; then
  gcloud run jobs update ml-similarity \
    --image=$ML_IMAGE \
    --region=$REGION
fi

# Create Evaluation Pipeline Job
echo "Creating ml-evaluation job..."
gcloud run jobs create ml-evaluation \
  --image=$ML_IMAGE \
  --region=$REGION \
  --add-cloudsql-instances=$PROJECT_ID:$REGION:shopsmart-db \
  --vpc-connector=shopsmart-connector \
  --set-secrets=DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest \
  --cpu=1 \
  --memory=1Gi \
  --max-retries=1 \
  --task-timeout=1h \
  --service-account=shopsmart-ml@$PROJECT_ID.iam.gserviceaccount.com \
  --command=python,-m,pipelines.evaluation \
  2>/dev/null || echo "ml-evaluation already exists, updating..."

if [ $? -ne 0 ]; then
  gcloud run jobs update ml-evaluation \
    --image=$ML_IMAGE \
    --region=$REGION
fi

echo ""
echo "✅ ML Cloud Run Jobs setup complete!"
echo ""
echo "Available jobs:"
echo "  - ml-data-loader: Load synthetic data into database"
echo "  - ml-trending: Calculate trending product scores"
echo "  - ml-similarity: Calculate product similarity matrix"
echo "  - ml-evaluation: Evaluate recommendation quality"
echo ""
echo "To run the data loader:"
echo "  gcloud run jobs execute ml-data-loader --region=$REGION --wait"
echo ""
echo "To run trending pipeline:"
echo "  gcloud run jobs execute ml-trending --region=$REGION --wait"
echo ""
