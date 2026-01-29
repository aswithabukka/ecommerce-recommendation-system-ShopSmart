#!/bin/bash
set -e

# ShopSmart GCP Infrastructure Setup Script
# This script automates the initial GCP infrastructure setup
# Run this once before deploying the application

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${PROJECT_ID:-"shopsmart-prod"}
REGION=${REGION:-"us-central1"}
ZONE=${ZONE:-"us-central1-a"}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ShopSmart GCP Infrastructure Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

# Step 1: Create and configure project
echo -e "${YELLOW}Step 1: Configuring GCP Project...${NC}"
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✓ Project configured${NC}"

# Step 2: Enable required APIs
echo -e "${YELLOW}Step 2: Enabling required APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    cloudscheduler.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    vpcaccess.googleapis.com \
    servicenetworking.googleapis.com \
    compute.googleapis.com

echo -e "${GREEN}✓ APIs enabled${NC}"

# Step 3: Create VPC Network
echo -e "${YELLOW}Step 3: Creating VPC Network...${NC}"
gcloud compute networks create shopsmart-vpc \
    --subnet-mode=custom \
    --bgp-routing-mode=regional || echo "VPC may already exist"

gcloud compute networks subnets create backend-subnet \
    --network=shopsmart-vpc \
    --region=$REGION \
    --range=10.0.1.0/24 || echo "Subnet may already exist"

echo -e "${GREEN}✓ VPC Network created${NC}"

# Step 4: Create Serverless VPC Connector
echo -e "${YELLOW}Step 4: Creating Serverless VPC Connector...${NC}"
gcloud compute networks vpc-access connectors create shopsmart-connector \
    --region=$REGION \
    --network=shopsmart-vpc \
    --range=10.8.0.0/28 \
    --min-throughput=200 \
    --max-throughput=1000 || echo "Connector may already exist"

echo -e "${GREEN}✓ VPC Connector created${NC}"

# Step 5: Create Service Accounts
echo -e "${YELLOW}Step 5: Creating Service Accounts...${NC}"

# Backend service account
gcloud iam service-accounts create shopsmart-backend \
    --display-name="ShopSmart Backend Service Account" || echo "Backend SA may already exist"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:shopsmart-backend@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:shopsmart-backend@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:shopsmart-backend@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"

# ML pipeline service account
gcloud iam service-accounts create shopsmart-ml \
    --display-name="ShopSmart ML Pipeline Service Account" || echo "ML SA may already exist"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:shopsmart-ml@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:shopsmart-ml@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:shopsmart-ml@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"

# Scheduler service account
gcloud iam service-accounts create shopsmart-scheduler \
    --display-name="ShopSmart Scheduler Service Account" || echo "Scheduler SA may already exist"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:shopsmart-scheduler@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

echo -e "${GREEN}✓ Service Accounts created and configured${NC}"

# Step 6: Create Artifact Registry
echo -e "${YELLOW}Step 6: Creating Artifact Registry...${NC}"
gcloud artifacts repositories create shopsmart \
    --repository-format=docker \
    --location=$REGION \
    --description="ShopSmart Docker images" || echo "Repository may already exist"

echo -e "${GREEN}✓ Artifact Registry created${NC}"

# Step 7: Provision Cloud SQL
echo -e "${YELLOW}Step 7: Provisioning Cloud SQL (this may take 5-10 minutes)...${NC}"
gcloud sql instances create shopsmart-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --network=shopsmart-vpc \
    --no-assign-ip \
    --enable-bin-log \
    --backup-start-time=03:00 \
    --database-flags=max_connections=100 || echo "Cloud SQL instance may already exist"

# Create database
gcloud sql databases create shopsmart \
    --instance=shopsmart-db || echo "Database may already exist"

# Create user
DB_PASSWORD=$(openssl rand -base64 32)
gcloud sql users create shopsmart \
    --instance=shopsmart-db \
    --password=$DB_PASSWORD || echo "User may already exist"

echo -e "${GREEN}✓ Cloud SQL provisioned${NC}"
echo -e "${YELLOW}Database password: $DB_PASSWORD${NC}"
echo -e "${YELLOW}Save this password securely!${NC}"

# Step 8: Provision Cloud Memorystore (Redis)
echo -e "${YELLOW}Step 8: Provisioning Cloud Memorystore (this may take 5-10 minutes)...${NC}"
gcloud redis instances create shopsmart-cache \
    --size=1 \
    --region=$REGION \
    --network=shopsmart-vpc \
    --redis-version=redis_7_0 \
    --tier=basic || echo "Redis instance may already exist"

echo -e "${GREEN}✓ Cloud Memorystore provisioned${NC}"

# Get Redis host
REDIS_HOST=$(gcloud redis instances describe shopsmart-cache --region=$REGION --format="value(host)")
echo -e "${YELLOW}Redis host: $REDIS_HOST${NC}"

# Step 9: Create Secrets
echo -e "${YELLOW}Step 9: Creating secrets...${NC}"

# Database URL
DB_CONNECTION_NAME="$PROJECT_ID:$REGION:shopsmart-db"
echo -n "postgresql://shopsmart:$DB_PASSWORD@/$DB_CONNECTION_NAME/shopsmart?host=/cloudsql/$DB_CONNECTION_NAME" | \
    gcloud secrets create database-url --data-file=- || echo "Secret may already exist"

# Redis URL
echo -n "redis://$REDIS_HOST:6379/0" | \
    gcloud secrets create redis-url --data-file=- || echo "Secret may already exist"

# CORS origins (update with your actual domain)
echo -n "https://shopsmart-frontend-REPLACE.a.run.app" | \
    gcloud secrets create cors-origins --data-file=- || echo "Secret may already exist"

echo -e "${GREEN}✓ Secrets created${NC}"

# Step 10: Enable pg_trgm extension
echo -e "${YELLOW}Step 10: Enabling PostgreSQL extensions...${NC}"
echo "Run this manually after setup:"
echo "  gcloud sql connect shopsmart-db --user=postgres"
echo "  CREATE EXTENSION IF NOT EXISTS pg_trgm;"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GCP Infrastructure Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Enable pg_trgm extension in PostgreSQL (see above)"
echo "2. Deploy backend: gcloud builds submit --config=backend/cloudbuild.yaml"
echo "3. Deploy frontend: gcloud builds submit --config=frontend/cloudbuild.yaml"
echo "4. Deploy ML pipelines: gcloud builds submit --config=ml/cloudbuild.yaml"
echo "5. Setup Cloud Scheduler for ML pipelines"
echo ""
echo "Important credentials:"
echo "  Database password: $DB_PASSWORD"
echo "  Redis host: $REDIS_HOST"
echo "  Cloud SQL connection: $DB_CONNECTION_NAME"
