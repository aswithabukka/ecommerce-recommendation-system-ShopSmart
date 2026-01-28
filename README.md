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

### Frontend
- **Framework**: React 18 with TypeScript
- **Routing**: React Router v6
- **Styling**: Tailwind CSS 3
- **HTTP Client**: Axios
- **State Management**: React Context API

### ML & Data Processing
- **Libraries**: NumPy, pandas, scikit-learn
- **Algorithms**: Cosine similarity, time-decay exponential scoring
- **Evaluation**: Recall, Precision, Hit Rate, NDCG

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Web Server**: Uvicorn (ASGI)
- **Development Server**: Vite (Frontend)

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

## 📚 Documentation

- **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)** - Comprehensive technical guide
- **[INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md)** - Interview preparation with Q&A
- **[CLAUDE.md](CLAUDE.md)** - Development guidelines and architecture notes
- **[STATUS.md](STATUS.md)** - Project status and feature checklist

## 🎯 Use Cases

1. **E-Commerce Platforms**: Product recommendations for online stores
2. **Content Discovery**: Adaptable for media, articles, or services
3. **Educational**: Learning recommendation systems and ML deployment
4. **Portfolio Projects**: Showcase full-stack and ML capabilities

## 🚦 Roadmap

### Phase 1 (Complete) ✅
- [x] Core recommendation engine
- [x] Trending algorithm
- [x] Event tracking system
- [x] Admin dashboard
- [x] Modern UI redesign

### Phase 2 (Planned)
- [ ] User authentication (JWT)
- [ ] Product reviews and ratings
- [ ] Wishlist functionality
- [ ] Email notifications
- [ ] A/B testing framework

### Phase 3 (Future)
- [ ] Deep learning recommendations
- [ ] Real-time ML updates
- [ ] Multi-armed bandit optimization
- [ ] Advanced analytics dashboard

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
