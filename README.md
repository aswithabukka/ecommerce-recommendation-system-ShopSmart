# ShopSmart - AI-Powered E-Commerce Recommendation System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18.0-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready, full-stack e-commerce recommendation system featuring collaborative filtering, trending algorithms, and real-time personalization. Built with modern technologies and designed for scalability.

## 🎯 Project Overview

ShopSmart is an intelligent product recommendation platform that delivers personalized shopping experiences through machine learning algorithms, real-time event tracking, and strategic caching. The system implements a three-tier recommendation fallback strategy to ensure every user receives relevant product suggestions, from cold-start scenarios to fully personalized experiences.

### Key Features

- **🤖 Intelligent Recommendations**: Item-to-item collaborative filtering with weighted event scoring
- **📈 Trending Products**: Time-decayed popularity algorithm with configurable time windows
- **⚡ Real-Time Tracking**: Event-driven architecture capturing views, cart additions, and purchases
- **🚀 High Performance**: Redis caching with intelligent invalidation strategies
- **📊 Analytics Dashboard**: Real-time insights into user behavior and product performance
- **🎨 Modern UI**: Clean, responsive interface inspired by leading e-commerce platforms
- **🔍 Advanced Search**: Full-text search with PostgreSQL trigrams and filtering
- **📱 Mobile Optimized**: Responsive design for all screen sizes

## 🏗️ Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend Layer                       │
│  React 18 + TypeScript + Tailwind CSS + React Router       │
│  [Home] [Product] [Search] [Cart] [Admin]                  │
└─────────────────┬───────────────────────────────────────────┘
                  │ REST API (Axios)
┌─────────────────▼───────────────────────────────────────────┐
│                       API Gateway Layer                      │
│           FastAPI + Uvicorn + Pydantic Validation          │
│  [Products] [Recommendations] [Events] [Admin]             │
└─────────────────┬───────────────────────────────────────────┘
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
┌──────────┐ ┌─────────┐ ┌──────────────┐
│PostgreSQL│ │  Redis  │ │ ML Pipelines │
│  Database│ │  Cache  │ │   (Python)   │
└──────────┘ └─────────┘ └──────────────┘
```

### Three-Tier Recommendation Strategy

```
User Request
     │
     ▼
┌─────────────────────────────────────┐
│  Has Interaction History?           │
├─────────────────────────────────────┤
│ YES → Collaborative Filtering       │
│       • Last 50 events              │
│       • Weighted by type            │
│       • Aggregated similarities     │
│                                     │
│ NO  → Cold Start Strategy           │
│       ├─ Category? → Trending       │
│       └─ None     → Global Trending │
└─────────────────────────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 15 (SQLAlchemy ORM)
- **Cache**: Redis 7
- **API Documentation**: OpenAPI (Swagger UI)
- **Validation**: Pydantic v2
- **Production Server**: Gunicorn + Uvicorn workers

### Frontend
- **Framework**: React 18 with TypeScript
- **Routing**: React Router v6
- **Styling**: Tailwind CSS 3
- **HTTP Client**: Axios
- **State Management**: React Context API
- **Build Tool**: Vite
- **Production Server**: Nginx

### ML & Data Processing
- **Libraries**: NumPy, pandas, scikit-learn
- **Algorithms**: Cosine similarity, time-decay exponential scoring
- **Evaluation**: Recall, Precision, Hit Rate, NDCG
- **Pipeline Orchestration**: Python modules with scheduled execution

### Cloud Infrastructure (GCP)
- **Compute**: Cloud Run (Serverless containers with autoscaling)
- **Database**: Cloud SQL for PostgreSQL 15
- **Cache**: Cloud Memorystore for Redis 7
- **Batch Processing**: Cloud Run Jobs (ML pipelines)
- **Scheduling**: Cloud Scheduler (Hourly/Daily pipeline automation)
- **CI/CD**: Cloud Build with GitHub integration
- **Networking**: VPC with Serverless VPC Connector
- **Container Registry**: Artifact Registry
- **Secrets**: Secret Manager
- **Monitoring**: Cloud Logging & Cloud Monitoring

### Development & Deployment
- **Containerization**: Docker + Docker Compose
- **Version Control**: Git + GitHub
- **Infrastructure as Code**: cloudbuild.yaml, docker-compose.yml
- **Deployment**: Automated via Cloud Build triggers

## 📊 System Performance

### Recommendation Quality Metrics
| Metric | @5 | @10 | @20 |
|--------|-----|-----|-----|
| **Recall** | 4.95% | 8.66% | 15.67% |
| **Precision** | 3.14% | 2.68% | 2.42% |
| **Hit Rate** | 13.86% | 22.63% | **36.95%** |
| **NDCG** | 0.0455 | 0.0581 | 0.0809 |

### Cache Performance
- **Hit Rate**: 33.3% (testing), 60-80% expected in production
- **TTLs**: 5min (recommendations), 1hr (similarities), 15min (trending)
- **Invalidation**: Event-driven + pipeline-triggered

### Database
- **Products**: 1,000 items across 8 categories
- **Users**: 500+ with interaction history
- **Events**: 50,000+ tracked interactions
- **Indexes**: 15+ optimized indexes for query performance

## 🚀 Quick Start

### Prerequisites
- Docker Desktop 4.0+
- Git 2.0+
- 4GB RAM minimum

### Installation

```bash
# Clone the repository
git clone https://github.com/aswithabukka/ecommerce-recommendation-system-ShopSmart.git
cd ecommerce-recommendation-system-ShopSmart

# Start all services
cd infra
docker compose up --build

# In a new terminal, load data and run ML pipelines
docker compose --profile ml run ml-pipeline python -m data.seed.synthetic_generator
docker compose --profile ml run ml-pipeline python -m pipelines.trending_pipeline
docker compose --profile ml run ml-pipeline python -m pipelines.similarity_pipeline

# Optional: Run evaluation
docker compose --profile ml run ml-pipeline python -m pipelines.evaluation
```

### Access Points
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Admin Dashboard**: http://localhost:3000/admin
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
shopsmart/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API routes and endpoints
│   │   ├── core/           # Core configuration (DB, Redis)
│   │   ├── models/         # Database models and schemas
│   │   ├── services/       # Business logic layer
│   │   └── main.py         # Application entry point
│   └── requirements.txt
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client and tracking
│   │   └── contexts/       # React contexts (Cart, etc.)
│   └── package.json
├── ml/                     # Machine learning pipelines
│   ├── pipelines/          # Trending, similarity, evaluation
│   └── data/              # Data loaders and generators
├── infra/                  # Infrastructure configuration
│   ├── docker-compose.yml
│   └── init.sql           # Database schema
└── docs/                   # Documentation
    ├── TECHNICAL_DOCUMENTATION.md
    └── INTERVIEW_GUIDE.md
```

## 🔑 Key Components

### 1. Recommendation Engine
- **Algorithm**: Item-to-item collaborative filtering
- **Features**: Event weighting (view=1x, cart=3x, purchase=5x)
- **Optimization**: Precomputed similarity matrix for fast lookups

### 2. Trending System
- **Algorithm**: Time-decayed exponential scoring
- **Windows**: 7-day and 30-day rolling windows
- **Formula**: `score = Σ(event_weight × e^(-λt))` where λ controls decay

### 3. Event Tracking
- **Events**: View, Add to Cart, Purchase
- **User Identity**: localStorage + sessionStorage for persistence
- **Processing**: Real-time with automatic cache invalidation

### 4. Caching Strategy
- **Architecture**: Namespace-based Redis keys
- **Invalidation**: User-specific + global patterns
- **Performance**: Sub-millisecond cache hits

### 5. Search System
- **Technology**: PostgreSQL full-text search with pg_trgm
- **Features**: Fuzzy matching, category filters, price ranges
- **Pagination**: Efficient offset-based pagination

## 📈 ML Pipeline Details

### Trending Pipeline
```python
# Computes popularity scores with time decay
# Runs: Hourly (recommended)
# Output: trending_scores table (2,000 rows)
# Algorithm: Exponential time decay

score = Σ(weight × e^(-λ × days_ago))
```

### Similarity Pipeline
```python
# Generates item-to-item similarity matrix
# Runs: Daily (recommended)
# Output: item_similarity table (50,000 pairs)
# Algorithm: Co-occurrence → Cosine similarity

similarity(i,j) = cosine(user_vector_i, user_vector_j)
```

### Evaluation Pipeline
```python
# Measures recommendation quality
# Runs: On-demand
# Metrics: Recall, Precision, Hit Rate, NDCG
# Split: Temporal (last 7 days as test set)
```

## 🔐 Security Features

- **Input Validation**: Pydantic schemas for all API requests
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **CORS Configuration**: Configurable allowed origins
- **Error Handling**: Comprehensive exception handling with logging
- **Rate Limiting**: Ready for implementation (infrastructure in place)

## 📊 API Endpoints

### Products
- `GET /products/` - Search and filter products
- `GET /products/{id}` - Get product details
- `GET /products/categories` - List all categories

### Recommendations
- `GET /recommendations` - Get personalized recommendations
- `GET /similar-products` - Get similar products

### Events
- `POST /events/` - Track user events

### Admin
- `GET /admin/dashboard` - Get analytics dashboard
- `POST /admin/cache/flush` - Flush cache

## 🧪 Testing

```bash
# Backend tests (when implemented)
cd backend
pytest tests/

# Frontend tests (when implemented)
cd frontend
npm test

# Manual API testing
# Visit http://localhost:8000/docs for interactive API documentation
```

## ☁️ Production Deployment (GCP)

ShopSmart is deployed to Google Cloud Platform with full autoscaling, managed databases, and automated ML pipelines.

### 🌐 Live Application

- **Frontend**: https://shopsmart-frontend-zy6q4fbfwq-uc.a.run.app
- **Backend API**: https://shopsmart-backend-780605319553.us-central1.run.app
- **API Documentation**: https://shopsmart-backend-780605319553.us-central1.run.app/docs

### Production Features

- ✅ **Autoscaling**: Backend (1-100 instances), Frontend (1-50 instances)
- ✅ **Managed Database**: Cloud SQL PostgreSQL 15 with automated backups
- ✅ **Distributed Cache**: Cloud Memorystore Redis 7 with 99.9% SLA
- ✅ **ML Pipelines**: Automated trending (hourly) and similarity (daily) updates via Cloud Run Jobs
- ✅ **CI/CD**: Automated builds and deployments via Cloud Build
- ✅ **Monitoring**: Cloud Logging and Cloud Monitoring integration
- ✅ **Secrets Management**: Secure credential storage with Secret Manager
- ✅ **VPC Networking**: Private network with serverless VPC connector

### Quick Deploy

```bash
# 1. Setup GCP infrastructure (VPC, Cloud SQL, Redis, etc.)
cd scripts
./setup-gcp.sh

# 2. Deploy backend service
cd backend
gcloud builds submit --config=cloudbuild.yaml

# 3. Deploy frontend service
cd frontend
gcloud builds submit --config=cloudbuild.yaml

# 4. Setup and run ML pipelines
cd scripts
./setup-ml-jobs.sh

# 5. Load initial data
gcloud run jobs execute ml-data-loader --region=us-central1 --wait
gcloud run jobs execute ml-trending --region=us-central1 --wait
gcloud run jobs execute ml-similarity --region=us-central1 --wait
```

### GCP Services Architecture

```
Users → Cloud Load Balancer
           ↓
    ┌──────┴──────┐
    ▼             ▼
Cloud Run      Cloud Run
(Backend)      (Frontend)
    ↓
    ├─→ Cloud SQL (PostgreSQL)
    ├─→ Cloud Memorystore (Redis)
    └─→ VPC Network

Cloud Scheduler → Cloud Run Jobs (ML Pipelines)
                      ↓
                  Cloud SQL + Redis
```

### GCP Services Used

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Cloud Run** | Serverless backend & frontend hosting | Backend: 1-100 instances, 512MB RAM<br>Frontend: 1-50 instances, 256MB RAM |
| **Cloud SQL** | Managed PostgreSQL database | PostgreSQL 15, db-f1-micro, Auto backups |
| **Cloud Memorystore** | Managed Redis cache | Redis 7, 1GB Basic tier |
| **Cloud Run Jobs** | Scheduled ML pipeline execution | 4 jobs: data-loader, trending, similarity, evaluation |
| **Cloud Scheduler** | Automated pipeline scheduling | Hourly trending, Daily similarity |
| **Cloud Build** | CI/CD pipeline | Auto-build on git push, 15min timeout |
| **Secret Manager** | Secure credential storage | DATABASE_URL, REDIS_URL, CORS_ORIGINS |
| **VPC Network** | Private networking | Serverless VPC connector for Cloud Run |
| **Artifact Registry** | Docker image storage | us-central1 Docker repository |
| **Cloud Logging** | Centralized logging | All services integrated |

### Cost Breakdown

**Startup Tier** (~$115-217/month):
- Cloud SQL (db-f1-micro): $7.50/month
- Cloud Memorystore (Basic 1GB): $35/month
- Cloud Run Backend: $50-100/month
- Cloud Run Frontend: $20-50/month
- Cloud Run Jobs (ML): $3-5/month
- Cloud Build: $0-20/month (free tier covers most)

**Production Tier** (~$620-970/month):
- Cloud SQL (db-custom-2-7680): $100/month
- Cloud Memorystore (Standard 5GB HA): $200/month
- Cloud Run Backend: $200-400/month
- Cloud Run Frontend: $100-200/month
- Cloud CDN: $20-50/month
- Other services: $50-100/month

### Complete Documentation

For detailed deployment instructions, troubleshooting, and maintenance guides:
- **[GCP Deployment Guide](docs/GCP_DEPLOYMENT.md)** - Complete deployment documentation
- **[Project Overview](docs/PROJECT_OVERVIEW.md)** - Comprehensive system architecture and cloud implementation
- **[Load Data Guide](LOAD_DATA.md)** - Step-by-step data loading instructions

## 🎯 Use Cases

1. **E-Commerce Platforms**: Product recommendations for online stores
2. **Content Discovery**: Adaptable for media, articles, or services
3. **Educational**: Learning recommendation systems and ML deployment
4. **Portfolio Projects**: Showcase full-stack and ML capabilities


## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- RetailRocket dataset for realistic e-commerce data
- FastAPI for the excellent async framework
- React community for amazing frontend tools
- Tailwind CSS for utility-first styling

## 📧 Contact

**Ashwitha Bukka**
- GitHub: [@aswithabukka](https://github.com/aswithabukka)
- Project Link: [https://github.com/aswithabukka/ecommerce-recommendation-system-ShopSmart](https://github.com/aswithabukka/ecommerce-recommendation-system-ShopSmart)

---

**Built with ❤️ using Python, React, and Machine Learning**
