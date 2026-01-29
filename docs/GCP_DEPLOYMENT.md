# GCP Production Deployment Guide

This guide provides step-by-step instructions for deploying ShopSmart to Google Cloud Platform (GCP) as a production-ready application with autoscaling, managed databases, and automated ML pipelines.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Cost Estimate](#cost-estimate)
- [Deployment Steps](#deployment-steps)
  - [Phase 1: Infrastructure Setup](#phase-1-infrastructure-setup)
  - [Phase 2: Deploy Backend](#phase-2-deploy-backend)
  - [Phase 3: Deploy Frontend](#phase-3-deploy-frontend)
  - [Phase 4: Deploy ML Pipelines](#phase-4-deploy-ml-pipelines)
  - [Phase 5: Setup CI/CD](#phase-5-setup-cicd)
  - [Phase 6: Setup Monitoring](#phase-6-setup-monitoring)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

## Prerequisites

### Required Tools

- **Google Cloud SDK** (gcloud CLI) - [Install](https://cloud.google.com/sdk/docs/install)
- **Docker** - [Install](https://docs.docker.com/get-docker/)
- **Git** - [Install](https://git-scm.com/downloads)

### GCP Account Setup

1. Create a GCP account: https://cloud.google.com/
2. Create a billing account
3. Have project creation permissions

### Environment Variables

Set these before running deployment scripts:

```bash
export PROJECT_ID="shopsmart-prod"  # Your GCP project ID
export REGION="us-central1"          # GCP region
export ZONE="us-central1-a"          # GCP zone
```

## Architecture Overview

```
┌─────────────┐
│   Users     │
└──────┬──────┘
       │ HTTPS
       │
┌──────▼───────────────┐
│  Cloud Load Balancer │
└──────┬───────────────┘
       │
┌──────▼────────────────────────────┐
│  Cloud Run Services               │
│  ┌────────────┐  ┌──────────────┐│
│  │  Backend   │  │  Frontend    ││
│  │  (FastAPI) │  │  (React)     ││
│  └─────┬──────┘  └──────────────┘│
└────────┼──────────────────────────┘
         │
    ┌────▼────┐
    │         │
┌───▼──┐  ┌──▼───┐
│Cloud │  │Cloud │
│SQL   │  │Memo  │
│(PG)  │  │Store │
└──────┘  └──────┘

Cloud Scheduler → Cloud Run Jobs (ML Pipelines)
```

**Components:**
- **Cloud Run**: Serverless containers with autoscaling (backend, frontend)
- **Cloud SQL**: Managed PostgreSQL 15
- **Cloud Memorystore**: Managed Redis 7
- **Cloud Run Jobs**: Scheduled ML pipelines
- **Cloud Scheduler**: Cron jobs (hourly/daily)
- **Cloud Build**: CI/CD pipelines
- **Secret Manager**: Credential storage
- **Artifact Registry**: Docker image storage

## Cost Estimate

### Startup Phase (~$115-217/month)

- Cloud SQL (db-f1-micro): **$7.50/month**
- Cloud Memorystore (Basic 1GB): **$35/month**
- Cloud Run Backend: **$50-100/month** (traffic-dependent)
- Cloud Run Frontend: **$20-50/month** (traffic-dependent)
- Cloud Run Jobs (ML): **$3-5/month**
- Cloud Build: **$0-20/month** (free tier: 120 min/day)
- **Total: $115-217/month**

### Production Phase (~$620-970/month)

- Cloud SQL (db-custom-1-3840): **$50/month**
- Cloud Memorystore (Standard 5GB HA): **$200/month**
- Cloud Run Backend: **$200-400/month**
- Cloud Run Frontend: **$100-200/month**
- Cloud CDN: **$20-50/month**
- Other services: **$50-100/month**
- **Total: $620-970/month**

**Cost Optimization Tips:**
- Use `min-instances=0` for Cloud Run to eliminate idle costs (adds ~2-3s cold start)
- Schedule Cloud SQL to stop during non-peak hours (save 50%)
- Use committed use discounts for Cloud SQL (37% discount for 1-year)

## Deployment Steps

### Phase 1: Infrastructure Setup

Run the automated setup script:

```bash
cd scripts
./setup-gcp.sh
```

This script will:
1. ✅ Configure GCP project
2. ✅ Enable required APIs
3. ✅ Create VPC network and subnets
4. ✅ Create Serverless VPC Connector
5. ✅ Create service accounts with IAM roles
6. ✅ Create Artifact Registry repository
7. ✅ Provision Cloud SQL (PostgreSQL 15)
8. ✅ Provision Cloud Memorystore (Redis 7)
9. ✅ Create secrets in Secret Manager

**Important:** Save the database password and Redis host displayed at the end!

#### Enable PostgreSQL Extension

```bash
gcloud sql connect shopsmart-db --user=postgres
```

In the PostgreSQL shell:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\q
```

#### Initialize Database Schema

Option 1: Run init.sql script
```bash
gcloud sql import sql shopsmart-db \
  gs://YOUR_BUCKET/init.sql \
  --database=shopsmart
```

Option 2: Use Alembic migrations (recommended for production)
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

### Phase 2: Deploy Backend

1. **Build and deploy backend:**

```bash
cd backend
gcloud builds submit --config=cloudbuild.yaml
```

2. **Verify deployment:**

```bash
# Get backend URL
BACKEND_URL=$(gcloud run services describe shopsmart-backend \
  --region=us-central1 \
  --format="value(status.url)")

# Test health endpoint
curl $BACKEND_URL/health

# Test API docs
open $BACKEND_URL/docs
```

Expected response from `/health`:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

### Phase 3: Deploy Frontend

1. **Update frontend Cloud Build config:**

Edit `frontend/cloudbuild.yaml` and replace `_BACKEND_URL` with your actual backend URL:

```yaml
substitutions:
  _BACKEND_URL: 'https://shopsmart-backend-ACTUAL_HASH.a.run.app'
```

2. **Build and deploy frontend:**

```bash
cd frontend
gcloud builds submit --config=cloudbuild.yaml
```

3. **Verify deployment:**

```bash
# Get frontend URL
FRONTEND_URL=$(gcloud run services describe shopsmart-frontend \
  --region=us-central1 \
  --format="value(status.url)")

# Test frontend
open $FRONTEND_URL
```

4. **Update CORS origins:**

```bash
echo -n "$FRONTEND_URL" | gcloud secrets versions add cors-origins --data-file=-

# Redeploy backend to pick up new CORS settings
cd backend
gcloud builds submit --config=cloudbuild.yaml
```

### Phase 4: Deploy ML Pipelines

1. **Build and push ML image:**

```bash
cd ml
gcloud builds submit --tag us-central1-docker.pkg.dev/$PROJECT_ID/shopsmart/ml:latest
```

2. **Create Cloud Run Jobs:**

```bash
# Trending Pipeline (hourly)
gcloud run jobs create ml-trending \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/shopsmart/ml:latest \
  --region=us-central1 \
  --vpc-connector=shopsmart-connector \
  --set-secrets=DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest \
  --service-account=shopsmart-ml@$PROJECT_ID.iam.gserviceaccount.com \
  --cpu=1 \
  --memory=512Mi \
  --max-retries=2 \
  --task-timeout=30m \
  --command=python,-m,pipelines.trending_pipeline

# Similarity Pipeline (daily)
gcloud run jobs create ml-similarity \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/shopsmart/ml:latest \
  --region=us-central1 \
  --vpc-connector=shopsmart-connector \
  --set-secrets=DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest \
  --service-account=shopsmart-ml@$PROJECT_ID.iam.gserviceaccount.com \
  --cpu=2 \
  --memory=4Gi \
  --max-retries=2 \
  --task-timeout=2h \
  --command=python,-m,pipelines.similarity_pipeline

# Evaluation Pipeline (weekly)
gcloud run jobs create ml-evaluation \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/shopsmart/ml:latest \
  --region=us-central1 \
  --vpc-connector=shopsmart-connector \
  --set-secrets=DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest \
  --service-account=shopsmart-ml@$PROJECT_ID.iam.gserviceaccount.com \
  --cpu=1 \
  --memory=1Gi \
  --max-retries=1 \
  --task-timeout=1h \
  --command=python,-m,pipelines.evaluation
```

3. **Load initial data:**

First, create a data loader job:
```bash
gcloud run jobs create ml-data-loader \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/shopsmart/ml:latest \
  --region=us-central1 \
  --vpc-connector=shopsmart-connector \
  --set-secrets=DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest \
  --service-account=shopsmart-ml@$PROJECT_ID.iam.gserviceaccount.com \
  --cpu=2 \
  --memory=2Gi \
  --max-retries=1 \
  --task-timeout=30m \
  --command=python,-m,data.seed.synthetic_generator
```

Run the data loader:
```bash
gcloud run jobs execute ml-data-loader --region=us-central1 --wait
```

4. **Run initial ML pipelines:**

```bash
# Run trending pipeline
gcloud run jobs execute ml-trending --region=us-central1 --wait

# Run similarity pipeline
gcloud run jobs execute ml-similarity --region=us-central1 --wait
```

5. **Setup Cloud Scheduler:**

```bash
# Hourly trending pipeline
gcloud scheduler jobs create http trending-hourly \
  --location=us-central1 \
  --schedule="0 * * * *" \
  --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/ml-trending:run" \
  --http-method=POST \
  --oauth-service-account-email=shopsmart-scheduler@$PROJECT_ID.iam.gserviceaccount.com

# Daily similarity pipeline (2 AM UTC)
gcloud scheduler jobs create http similarity-daily \
  --location=us-central1 \
  --schedule="0 2 * * *" \
  --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/ml-similarity:run" \
  --http-method=POST \
  --oauth-service-account-email=shopsmart-scheduler@$PROJECT_ID.iam.gserviceaccount.com

# Weekly evaluation (Sunday 3 AM UTC)
gcloud scheduler jobs create http evaluation-weekly \
  --location=us-central1 \
  --schedule="0 3 * * 0" \
  --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/ml-evaluation:run" \
  --http-method=POST \
  --oauth-service-account-email=shopsmart-scheduler@$PROJECT_ID.iam.gserviceaccount.com
```

### Phase 5: Setup CI/CD

Connect your GitHub repository to Cloud Build:

```bash
# Backend trigger
gcloud builds triggers create github \
  --name=deploy-backend \
  --repo-name=ecommerce-recommendation-system-ShopSmart \
  --repo-owner=aswithabukka \
  --branch-pattern=^main$ \
  --build-config=backend/cloudbuild.yaml \
  --included-files=backend/**

# Frontend trigger
gcloud builds triggers create github \
  --name=deploy-frontend \
  --repo-name=ecommerce-recommendation-system-ShopSmart \
  --repo-owner=aswithabukka \
  --branch-pattern=^main$ \
  --build-config=frontend/cloudbuild.yaml \
  --included-files=frontend/**

# ML pipelines trigger
gcloud builds triggers create github \
  --name=build-ml \
  --repo-name=ecommerce-recommendation-system-ShopSmart \
  --repo-owner=aswithabukka \
  --branch-pattern=^main$ \
  --build-config=ml/cloudbuild.yaml \
  --included-files=ml/**
```

Now, any push to the `main` branch will automatically trigger builds and deployments!

### Phase 6: Setup Monitoring

1. **Create monitoring dashboard:**

Go to Cloud Console → Monitoring → Dashboards → Create Dashboard

Add charts for:
- Cloud Run request rate
- Cloud Run latency (p50, p95, p99)
- Cloud Run error rate
- Cloud SQL CPU utilization
- Cloud SQL connections
- Cloud Memorystore memory usage
- Cloud Memorystore hit rate
- ML pipeline execution time

2. **Setup alerting:**

```bash
# Backend service down alert
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Backend Service Down" \
  --condition-display-name="Backend Unhealthy" \
  --condition-threshold-value=1 \
  --condition-threshold-duration=300s \
  --condition-threshold-filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count"'

# High error rate alert
# ... (add more alerts as needed)
```

3. **Setup budget alerts:**

```bash
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="ShopSmart Monthly Budget" \
  --budget-amount=500 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=75 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

## Verification

### Backend Health Check

```bash
curl https://shopsmart-backend-HASH.a.run.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

### Frontend Check

```bash
curl https://shopsmart-frontend-HASH.a.run.app/
```

Should return React app HTML.

### Database Verification

```bash
gcloud sql connect shopsmart-db --user=shopsmart

# In PostgreSQL shell:
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM events;
SELECT COUNT(*) FROM trending_scores;
SELECT COUNT(*) FROM item_similarity;
```

### ML Pipeline Verification

```bash
# Check job execution history
gcloud run jobs executions list --job=ml-trending --region=us-central1

# View logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=ml-trending" --limit=50
```

## Troubleshooting

### Backend not connecting to Cloud SQL

**Symptoms:** Backend returns 500 errors, logs show database connection errors

**Solutions:**
1. Verify VPC connector is attached:
   ```bash
   gcloud run services describe shopsmart-backend --region=us-central1 --format="value(spec.template.spec.vpcAccess.connector)"
   ```

2. Check database secret:
   ```bash
   gcloud secrets versions access latest --secret=database-url
   ```

3. Verify Cloud SQL instance is running:
   ```bash
   gcloud sql instances list
   ```

### Redis connection timeout

**Symptoms:** Cache operations fail, logs show Redis timeout errors

**Solutions:**
1. Get Redis host IP:
   ```bash
   gcloud redis instances describe shopsmart-cache --region=us-central1 --format="value(host)"
   ```

2. Update Redis URL secret:
   ```bash
   echo -n "redis://REDIS_IP:6379/0" | gcloud secrets versions add redis-url --data-file=-
   ```

3. Redeploy backend:
   ```bash
   cd backend && gcloud builds submit --config=cloudbuild.yaml
   ```

### ML Pipeline out of memory

**Symptoms:** Similarity pipeline fails with OOM errors

**Solutions:**
1. Increase memory allocation:
   ```bash
   gcloud run jobs update ml-similarity --memory=8Gi --region=us-central1
   ```

2. Reduce batch size in similarity pipeline (edit `ml/pipelines/similarity_pipeline.py`, line ~50):
   ```python
   batch_size = 100  # Reduced from 500
   ```

### Frontend returns 404 for routes

**Symptoms:** Direct navigation to `/product/123` returns 404

**Solution:** Verify nginx config has SPA fallback (should already be in `nginx-production.conf`):
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### CI/CD build failures

**Symptoms:** Cloud Build triggers fail

**Solutions:**
1. Check build logs:
   ```bash
   gcloud builds list --limit=5
   gcloud builds log BUILD_ID
   ```

2. Verify service account permissions:
   ```bash
   gcloud projects get-iam-policy $PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com"
   ```

3. Grant missing roles:
   ```bash
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
     --role="roles/run.admin"
   ```

## Maintenance

### Updating Services

**Backend update:**
```bash
cd backend
gcloud builds submit --config=cloudbuild.yaml
```

**Frontend update:**
```bash
cd frontend
gcloud builds submit --config=cloudbuild.yaml
```

**ML pipelines update:**
```bash
cd ml
gcloud builds submit --config=cloudbuild.yaml
```

### Database Backups

Cloud SQL automatically backs up daily. To create manual backup:
```bash
gcloud sql backups create --instance=shopsmart-db
```

To restore from backup:
```bash
gcloud sql backups list --instance=shopsmart-db
gcloud sql backups restore BACKUP_ID --backup-instance=shopsmart-db
```

### Scaling Resources

**Increase Cloud SQL capacity:**
```bash
gcloud sql instances patch shopsmart-db --tier=db-custom-2-7680
```

**Increase Redis capacity:**
```bash
gcloud redis instances update shopsmart-cache --size=5 --region=us-central1
```

**Increase Cloud Run instances:**
```bash
gcloud run services update shopsmart-backend \
  --max-instances=200 \
  --region=us-central1
```

### Monitoring Costs

View current costs:
```bash
gcloud billing accounts list
gcloud billing accounts get-iam-policy BILLING_ACCOUNT_ID
```

View cost breakdown:
- Go to Cloud Console → Billing → Reports
- Filter by service to see costs for Cloud Run, Cloud SQL, etc.

### Security Best Practices

1. **Rotate secrets regularly:**
   ```bash
   # Generate new database password
   NEW_PASSWORD=$(openssl rand -base64 32)
   gcloud sql users set-password shopsmart --instance=shopsmart-db --password=$NEW_PASSWORD

   # Update secret
   echo -n "postgresql://shopsmart:$NEW_PASSWORD@/..." | gcloud secrets versions add database-url --data-file=-
   ```

2. **Review IAM permissions:**
   ```bash
   gcloud projects get-iam-policy $PROJECT_ID
   ```

3. **Enable audit logging:**
   ```bash
   # Already enabled by default for admin activities
   # Check: Cloud Console → Logging → Logs Explorer
   ```

4. **Use VPC Service Controls (optional, for high security):**
   ```bash
   gcloud access-context-manager policies create --title="ShopSmart Perimeter"
   ```

## Next Steps

- [ ] Set up custom domain with Cloud Load Balancing
- [ ] Enable Cloud CDN for frontend static assets
- [ ] Configure Cloud Armor for DDoS protection
- [ ] Set up oncall rotation and incident response
- [ ] Run load tests and optimize performance
- [ ] Configure database read replicas for high availability
- [ ] Set up multi-region deployment for global availability

## Support

- GCP Documentation: https://cloud.google.com/docs
- Cloud Run Documentation: https://cloud.google.com/run/docs
- Cloud SQL Documentation: https://cloud.google.com/sql/docs
- Project Repository: https://github.com/aswithabukka/ecommerce-recommendation-system-ShopSmart
- Technical Documentation: [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)
- Interview Guide: [INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md)
