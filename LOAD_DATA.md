# Load Data into Production Database

The frontend is showing "Failed to load recommendations" because the database is empty. Follow these steps to populate it:

## Step 1: Run the Data Loader Job

This will populate the database with 1000 products, 500 users, and 50,000 events.

```bash
gcloud run jobs execute ml-data-loader \
  --region=us-central1 \
  --wait
```

Expected output:
```
Generating synthetic data...
  Products: 1000
  Users: 500
  Events: 50000
  Time span: 90 days

Clearing existing data...
Data cleared successfully
...
✅ Execution [xxx] completed. Created 1000 products
```

## Step 2: Run the Trending Pipeline

This calculates which products are trending based on recent events.

```bash
gcloud run jobs execute ml-trending \
  --region=us-central1 \
  --wait
```

Expected output:
```
Starting trending pipeline...
Processing events from last 7 days...
✅ Trending scores calculated for 1000 products
```

## Step 3: Run the Similarity Pipeline

This calculates which products are similar to each other.

```bash
gcloud run jobs execute ml-similarity \
  --region=us-central1 \
  --wait
```

Expected output:
```
Starting similarity pipeline...
Processing 1000 products in batches of 500...
✅ Similarity matrix calculated (50,000 product pairs)
```

## Step 4: Verify Data Loaded

Refresh your frontend URL and you should now see:
- Products in the "Shop by Category" section
- Trending products displayed
- Recommendations working

Frontend URL: https://shopsmart-frontend-zy6q4fbfwq-uc.a.run.app

## Troubleshooting

### If data loader fails:

Check the job logs:
```bash
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=ml-data-loader" \
  --limit=50 \
  --format=json
```

### If trending/similarity fails:

Make sure the data loader completed successfully first. Check logs:
```bash
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=ml-trending" \
  --limit=50 \
  --format=json
```

### Verify database has data:

Connect to Cloud SQL and check:
```bash
gcloud sql connect shopsmart-db --user=postgres --database=shopsmart
```

Then run:
```sql
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM events;
SELECT COUNT(*) FROM trending_scores;
SELECT COUNT(*) FROM item_similarity;
```

Expected counts:
- products: 1000
- events: 50000
- trending_scores: ~1000 (varies)
- item_similarity: ~50000 (top 50 per product)

## Automated Scheduling (Optional)

To run these pipelines automatically:

```bash
# Hourly trending updates
gcloud scheduler jobs create http trending-hourly \
  --location=us-central1 \
  --schedule="0 * * * *" \
  --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/shopsmart-prod/jobs/ml-trending:run" \
  --http-method=POST \
  --oauth-service-account-email=shopsmart-ml@shopsmart-prod.iam.gserviceaccount.com

# Daily similarity updates (2 AM UTC)
gcloud scheduler jobs create http similarity-daily \
  --location=us-central1 \
  --schedule="0 2 * * *" \
  --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/shopsmart-prod/jobs/ml-similarity:run" \
  --http-method=POST \
  --oauth-service-account-email=shopsmart-ml@shopsmart-prod.iam.gserviceaccount.com
```
