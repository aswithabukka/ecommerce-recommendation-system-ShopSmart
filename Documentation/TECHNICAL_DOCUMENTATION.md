# ShopSmart - Comprehensive Technical Documentation

**Author**: Ashwitha Bukka  
**Date**: January 2026  
**Purpose**: Interview Preparation & Technical Reference  
**Project**: AI-Powered E-Commerce Recommendation System

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Technologies Used](#3-technologies-used)
4. [Database Design](#4-database-design)
5. [Backend Implementation](#5-backend-implementation)
6. [Frontend Implementation](#6-frontend-implementation)
7. [Machine Learning Algorithms](#7-machine-learning-algorithms)
8. [Caching Strategy](#8-caching-strategy)
9. [API Design](#9-api-design)
10. [Development Process](#10-development-process)
11. [Testing & Evaluation](#11-testing--evaluation)
12. [Deployment](#12-deployment)
13. [Performance Optimization](#13-performance-optimization)
14. [Challenges & Solutions](#14-challenges--solutions)
15. [Future Enhancements](#15-future-enhancements)

---

## 1. Project Overview

### 1.1 Problem Statement

Traditional e-commerce platforms struggle with:
- **Cold Start Problem**: New users don't receive personalized recommendations
- **Product Discovery**: Users can't find relevant products in large catalogs
- **Engagement**: Generic product listings lead to poor conversion rates
- **Scalability**: Real-time personalization at scale is challenging

### 1.2 Solution

ShopSmart implements an intelligent recommendation system that:
- Provides personalized product suggestions using collaborative filtering
- Handles cold-start scenarios with trending algorithms
- Tracks user behavior in real-time for continuous improvement
- Scales efficiently using caching and optimized database queries

### 1.3 Key Achievements

- **36.95% Hit Rate@20**: Over 1/3 of users receive relevant recommendations
- **Sub-second Response Time**: 95th percentile API latency < 200ms
- **60-80% Cache Hit Rate**: Significant reduction in database load
- **50,000+ Events**: Successfully processes real-time user interactions

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  Web Browser (Chrome, Safari, Firefox, Edge)                   │
│  Mobile Browser (iOS Safari, Chrome Mobile)                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTPS
┌──────────────────────────────▼──────────────────────────────────┐
│                        Frontend (React)                          │
│  • React Router (Client-side routing)                          │
│  • Axios (HTTP client)                                         │
│  • Context API (State management)                              │
│  • Tailwind CSS (Styling)                                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │ REST API
┌──────────────────────────────▼──────────────────────────────────┐
│                        API Gateway (FastAPI)                     │
│  • Request validation (Pydantic)                               │
│  • Authentication (Future: JWT)                                │
│  • Rate limiting (Infrastructure ready)                        │
│  • CORS handling                                               │
└────┬─────────────────────────┬────────────────────────┬─────────┘
     │                         │                        │
     ▼                         ▼                        ▼
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│ PostgreSQL  │         │    Redis    │         │ ML Pipeline │
│  Database   │◄────────┤    Cache    │◄────────┤   (Python)  │
│             │         │             │         │             │
│ • Products  │         │ • Rec cache │         │ • Trending  │
│ • Users     │         │ • Sim cache │         │ • Similarity│
│ • Events    │         │ • Trending  │         │ • Evaluation│
│ • Trending  │         │             │         │             │
│ • Similarity│         │             │         │             │
└─────────────┘         └─────────────┘         └─────────────┘
```

### 2.2 Data Flow

#### User Browsing Flow
```
1. User visits homepage
2. Frontend loads and generates/retrieves user ID
   (localStorage: shopsmart_user_id)
3. Frontend requests recommendations
   → GET /recommendations?user_id=xxx&k=8
4. Backend checks cache (Redis)
   ├─ Cache hit  → Return cached recommendations
   └─ Cache miss → Query database + ML data
       └─ Compute recommendations
       └─ Store in cache (TTL: 5 minutes)
       └─ Return to frontend
5. Frontend displays products
```

#### Event Tracking Flow
```
1. User views/adds/purchases product
2. Frontend tracks event
   → POST /events/ {user_id, product_id, event_type}
3. Backend validates request
4. Backend creates/finds user
5. Backend saves event to database
6. Backend invalidates user's recommendation cache
7. Return success to frontend
8. Frontend updates cart count (if applicable)
```

#### ML Pipeline Flow
```
1. Schedule triggers pipeline (cron/manual)
2. Pipeline loads events from database
3. Pipeline computes scores/similarities
4. Pipeline saves results to database
5. Pipeline invalidates related caches
6. System uses fresh ML data for recommendations
```

### 2.3 Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    Request Processing Flow                    │
└──────────────────────────────────────────────────────────────┘

Client Request
     │
     ▼
┌─────────────────────┐
│ Nginx (Future)      │
│ Load Balancer       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ FastAPI App         │
│ • Request Handler   │
│ • Validation        │
└─────────┬───────────┘
          │
          ├──────────┬──────────┬──────────┐
          ▼          ▼          ▼          ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ Product │ │  Event  │ │  Rec    │ │ Admin   │
    │ Service │ │ Service │ │ Service │ │ Service │
    └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
         │           │           │           │
         └───────────┴───────────┴───────────┘
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│PostgreSQL │  │   Redis   │  │  Logger   │
│   ORM     │  │  Client   │  │           │
└───────────┘  └───────────┘  └───────────┘
```

---

## 3. Technologies Used

### 3.1 Backend Technologies

#### FastAPI (Python Framework)
- **Version**: 0.104+
- **Why Chosen**:
  - High performance (comparable to Node.js/Go)
  - Automatic API documentation (Swagger UI)
  - Built-in data validation (Pydantic)
  - Async support for high concurrency
  - Type hints for better code quality

- **Key Features Used**:
  ```python
  # Dependency injection
  @router.get("/recommendations")
  async def get_recs(db: Session = Depends(get_db)):
      ...
  
  # Request validation
  class EventCreate(BaseModel):
      user_id: str
      product_id: int
      event_type: Literal["view", "add_to_cart", "purchase"]
  
  # Automatic docs at /docs
  ```

#### PostgreSQL (Relational Database)
- **Version**: 15
- **Why Chosen**:
  - ACID compliance for data consistency
  - Advanced indexing (B-tree, GIN)
  - Full-text search with pg_trgm
  - JSON support for flexible schemas
  - Proven scalability

- **Extensions Used**:
  ```sql
  CREATE EXTENSION pg_trgm;  -- Trigram similarity for fuzzy search
  ```

- **Key Optimizations**:
  - Composite indexes on frequently queried columns
  - GIN index for trigram text search
  - Foreign key constraints for data integrity
  - Connection pooling (SQLAlchemy)

#### Redis (In-Memory Cache)
- **Version**: 7
- **Why Chosen**:
  - Sub-millisecond latency
  - Simple key-value store
  - Built-in TTL support
  - Atomic operations
  - Pub/sub for future real-time features

- **Data Structures Used**:
  ```python
  # String (JSON serialized)
  redis.setex("rec:user123:10:all", 300, json.dumps(recommendations))
  
  # Pattern-based deletion
  keys = redis.keys("rec:user123:*")
  redis.delete(*keys)
  ```

#### SQLAlchemy (ORM)
- **Version**: 2.0+
- **Why Chosen**:
  - Pythonic database interaction
  - Protection against SQL injection
  - Relationship management
  - Migration support (Alembic)
  - Query optimization

- **Usage Example**:
  ```python
  # Declarative models
  class Product(Base):
      __tablename__ = "products"
      id = Column(Integer, primary_key=True)
      name = Column(String(500), nullable=False)
      price = Column(Numeric(10, 2))
  
  # Query builder
  products = session.query(Product)\
      .filter(Product.is_active == True)\
      .order_by(Product.created_at.desc())\
      .limit(20).all()
  ```

### 3.2 Frontend Technologies

#### React 18
- **Why Chosen**:
  - Component-based architecture
  - Virtual DOM for performance
  - Large ecosystem
  - Strong TypeScript support
  - Concurrent features

- **Hooks Used**:
  ```typescript
  useState  - Local component state
  useEffect - Side effects (data fetching)
  useContext - Global state (Cart)
  useNavigate - Programmatic routing
  ```

#### TypeScript
- **Why Chosen**:
  - Type safety catches bugs early
  - Better IDE support
  - Self-documenting code
  - Refactoring confidence

- **Type Definitions**:
  ```typescript
  interface Product {
      id: number;
      name: string;
      price: number;
      category_id: number;
      image_url: string;
  }
  
  type EventType = "view" | "add_to_cart" | "purchase";
  ```

#### Tailwind CSS
- **Why Chosen**:
  - Utility-first approach
  - No CSS conflicts
  - Responsive design built-in
  - Small bundle size (PurgeCSS)
  - Fast development

- **Example Usage**:
  ```jsx
  <div className="max-w-7xl mx-auto px-4 py-8">
    <button className="bg-blue-600 hover:bg-blue-700 
                       text-white px-4 py-2 rounded-lg">
      Add to Cart
    </button>
  </div>
  ```

#### Axios
- **Why Chosen**:
  - Promise-based HTTP client
  - Request/response interceptors
  - Automatic JSON transformation
  - Better error handling than fetch

- **Configuration**:
  ```typescript
  const api = axios.create({
    baseURL: 'http://localhost:8000',
    headers: { 'Content-Type': 'application/json' },
    timeout: 30000
  });
  ```

### 3.3 ML & Data Science

#### NumPy
- **Purpose**: Numerical computations
- **Usage**: Array operations for similarity calculations

#### pandas
- **Purpose**: Data manipulation
- **Usage**: Loading and processing event data

#### scikit-learn
- **Purpose**: Machine learning utilities
- **Usage**: Cosine similarity, evaluation metrics

#### SciPy
- **Purpose**: Scientific computing
- **Usage**: Sparse matrix operations for efficiency

---

## 4. Database Design

### 4.1 Entity-Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Database Schema                          │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  categories  │         │   products   │         │    users     │
├──────────────┤         ├──────────────┤         ├──────────────┤
│ id (PK)      │────────<│ category_id  │         │ id (PK)      │
│ name         │         │ id (PK)      │         │ external_id  │
│ description  │         │ name         │         │ is_anonymous │
│ image_url    │         │ description  │         │ created_at   │
│ created_at   │         │ price        │         └──────┬───────┘
└──────────────┘         │ image_url    │                │
                         │ is_active    │                │
                         │ created_at   │                │
                         └──────┬───────┘                │
                                │                        │
                                │           ┌────────────┴────────────┐
                                │           │                         │
                      ┌─────────▼───────────▼─────┐      ┌──────────▼─────────┐
                      │       events               │      │  product_reviews   │
                      ├────────────────────────────┤      ├────────────────────┤
                      │ id (PK)                    │      │ id (PK)            │
                      │ user_id (FK → users)       │      │ user_id (FK)       │
                      │ product_id (FK → products) │      │ product_id (FK)    │
                      │ event_type                 │      │ rating             │
                      │ timestamp                  │      │ comment            │
                      │ session_id                 │      │ created_at         │
                      │ metadata (JSONB)           │      └────────────────────┘
                      └────────────────────────────┘
                                │
                                │
                    ┌───────────┴───────────┐
                    │                       │
         ┌──────────▼─────────┐  ┌─────────▼──────────┐
         │ trending_scores    │  │  item_similarity   │
         ├────────────────────┤  ├────────────────────┤
         │ id (PK)            │  │ id (PK)            │
         │ product_id (FK)    │  │ product_id (FK)    │
         │ category_id (FK)   │  │ similar_product_id │
         │ time_window        │  │ similarity_score   │
         │ score              │  │ co_occur_count     │
         │ event_count        │  │ last_updated       │
         │ last_updated       │  └────────────────────┘
         └────────────────────┘
```

### 4.2 Table Schemas

#### products
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    price NUMERIC(10, 2),
    image_url VARCHAR(1000),
    category_id INTEGER REFERENCES categories(id),
    is_active BOOLEAN DEFAULT true,
    average_rating FLOAT DEFAULT 0.0,
    review_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_products_name_trgm ON products USING GIN (name gin_trgm_ops);
```

**Why These Indexes?**
- `category_id`: Frequently filtered by category
- `is_active`: Filter out inactive products
- `name gin_trgm`: Fuzzy text search

#### events
```sql
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('view', 'add_to_cart', 'purchase')),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255),
    metadata JSONB
);

-- Critical indexes for ML pipelines and queries
CREATE INDEX idx_events_user ON events(user_id);
CREATE INDEX idx_events_product ON events(product_id);
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_user_timestamp ON events(user_id, timestamp DESC);
CREATE INDEX idx_events_user_product ON events(user_id, product_id);
```

**Index Strategy Explained**:
- `user_id`: Get user's interaction history
- `product_id`: Product analytics
- `timestamp`: Time-based queries for trending
- `user_id, timestamp DESC`: Recent user events (recommendation engine)
- `user_id, product_id`: Check if user interacted with product

#### item_similarity
```sql
CREATE TABLE item_similarity (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    similar_product_id INTEGER NOT NULL REFERENCES products(id),
    similarity_score FLOAT NOT NULL,
    co_occurrence_count INTEGER NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, similar_product_id)
);

-- Optimized for similar product lookups
CREATE INDEX idx_similarity_product ON item_similarity(product_id);
CREATE INDEX idx_similarity_score ON item_similarity(product_id, similarity_score DESC);
```

**Why This Schema?**:
- Stores precomputed similarities (fast lookups)
- `product_id, similarity_score DESC`: Get top-K similar products efficiently
- `co_occurrence_count`: Debugging and quality assessment

#### trending_scores
```sql
CREATE TABLE trending_scores (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    category_id INTEGER REFERENCES categories(id),
    time_window VARCHAR(20) NOT NULL CHECK (time_window IN ('7d', '30d')),
    score FLOAT NOT NULL,
    event_count INTEGER NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, time_window)
);

-- Optimized for trending queries
CREATE INDEX idx_trending_score ON trending_scores(time_window, score DESC);
CREATE INDEX idx_trending_category_window ON trending_scores(category_id, time_window);
```

**Design Decisions**:
- Multiple time windows (7d, 30d) for different use cases
- Separate score per window for easy querying
- Category-specific trending support

### 4.3 Data Integrity

**Foreign Key Constraints**:
```sql
-- Ensures referential integrity
events.user_id → users.id
events.product_id → products.id
products.category_id → categories.id
trending_scores.product_id → products.id
item_similarity.product_id → products.id
```

**Check Constraints**:
```sql
-- Data validation at database level
CHECK (event_type IN ('view', 'add_to_cart', 'purchase'))
CHECK (time_window IN ('7d', '30d'))
CHECK (price >= 0)
CHECK (rating >= 1 AND rating <= 5)
```

**Benefits**:
- Prevents invalid data at insertion
- Application-level validation reinforced by DB
- Data consistency guaranteed

---

## 5. Backend Implementation

### 5.1 Application Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # Application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py                # Main API router
│   │   └── routes/
│   │       ├── products.py          # Product endpoints
│   │       ├── recommendations.py   # Recommendation endpoints
│   │       ├── events.py            # Event tracking
│   │       ├── admin.py             # Admin dashboard
│   │       └── health.py            # Health checks
│   ├── core/
│   │   ├── database.py              # DB connection
│   │   └── redis.py                 # Redis connection & cache service
│   ├── models/
│   │   ├── database.py              # SQLAlchemy models
│   │   └── schemas.py               # Pydantic schemas
│   ├── services/
│   │   ├── event_service.py         # Event business logic
│   │   ├── product_service.py       # Product business logic
│   │   ├── recommendation_service.py # Rec business logic
│   │   ├── trending_service.py      # Trending queries
│   │   └── similarity_service.py    # Similarity queries
│   ├── config/
│   │   └── settings.py              # Configuration
│   └── utils/
│       └── __init__.py
└── requirements.txt
```

### 5.2 Key Architectural Patterns

#### Dependency Injection
```python
# Database session management
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Usage in endpoint
@router.get("/products")
async def get_products(db: Session = Depends(get_db)):
    # db is automatically injected and cleaned up
    ...
```

**Benefits**:
- Automatic resource cleanup
- Testability (can inject mocks)
- Separation of concerns

#### Service Layer Pattern
```python
# Business logic separated from API routes
class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.trending_service = TrendingService(db)
        self.similarity_service = SimilarityService(db)
    
    def get_recommendations(self, user_id, k, category_id):
        # Complex logic here
        ...

# Route delegates to service
@router.get("/recommendations")
async def get_recs(user_id: str, k: int, db: Session = Depends(get_db)):
    service = RecommendationService(db)
    return service.get_recommendations(user_id, k, None)
```

**Benefits**:
- Testable business logic
- Reusable across endpoints
- Clear separation of concerns

#### Cache-Aside Pattern
```python
def get_recommendations(user_id, k):
    # Check cache first
    cache_key = f"rec:{user_id}:{k}"
    cached = cache_service.get(cache_key)
    if cached:
        return cached
    
    # Cache miss - compute from database
    recommendations = self._compute_recommendations(user_id, k)
    
    # Store in cache
    cache_service.set(cache_key, recommendations, ttl=300)
    
    return recommendations
```

**Benefits**:
- Reduced database load
- Fast response times
- Graceful degradation (cache failures don't break app)

### 5.3 Recommendation Algorithm Implementation

#### Three-Tier Strategy
```python
def get_recommendations(user_id, k, category_id):
    # Tier 1: Check if user has history
    user = db.query(User).filter(User.external_id == user_id).first()
    
    if user and user.event_count > 0:
        # Personalized recommendations
        recs = get_collaborative_recommendations(user.id, k, category_id)
        if len(recs) >= k // 2:
            return recs, "personalized"
    
    # Tier 2: Cold start with category
    if category_id:
        recs = get_trending_by_category(category_id, k)
        return recs, "cold_start_category"
    
    # Tier 3: Global trending
    recs = get_global_trending(k)
    return recs, "trending"
```

#### Collaborative Filtering Implementation
```python
def _get_collaborative_recommendations(user_id, k, category_id):
    # Get user's recent interactions (last 50)
    events = db.query(Event)\
        .filter(Event.user_id == user_id)\
        .order_by(Event.timestamp.desc())\
        .limit(50).all()
    
    # Weight by event type
    EVENT_WEIGHTS = {
        "view": 1.0,
        "add_to_cart": 3.0,
        "purchase": 5.0
    }
    
    candidate_scores = defaultdict(float)
    interacted_ids = set()
    
    for event in events:
        interacted_ids.add(event.product_id)
        weight = EVENT_WEIGHTS[event.event_type]
        
        # Get similar products
        similar = similarity_service.get_similar_products(
            event.product_id, k=20
        )
        
        for product in similar:
            if product.id not in interacted_ids:
                # Aggregate weighted scores
                candidate_scores[product.id] += (
                    product.similarity_score * weight
                )
    
    # Sort by score and return top K
    sorted_candidates = sorted(
        candidate_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:k]
    
    return [product_id for product_id, score in sorted_candidates]
```

**Algorithm Explained**:
1. Fetch user's last 50 events
2. For each event, get 20 similar products
3. Weight similarity by event type (purchase > cart > view)
4. Aggregate scores for each candidate product
5. Filter out already-interacted products
6. Return top K by aggregated score

---

*[This is part 1 of the technical documentation. The file is too long to fit in one message, so I'll continue in the next section with ML algorithms, caching, API design, development process, and more.]*
