# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Docker (Primary Development)

```bash
# Start all services
cd infra && docker compose up --build

# Start with ML pipeline profile
docker compose --profile ml up --build

# Run ML pipelines (after data is loaded)
docker compose --profile ml run ml-pipeline python -m pipelines.trending_pipeline
docker compose --profile ml run ml-pipeline python -m pipelines.similarity_pipeline
docker compose --profile ml run ml-pipeline python -m pipelines.evaluation

# Load data
docker compose --profile ml run ml-pipeline python -m data.seed.synthetic_generator
docker compose --profile ml run ml-pipeline python -m data.seed.retailrocket_loader

# Access running containers
docker exec -it shopsmart-api bash
docker exec -it shopsmart-ml python
```

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# ML Pipelines
cd ml
pip install -r requirements.txt
python -m pipelines.trending_pipeline
```

### Database Operations

```bash
# Direct PostgreSQL access
docker exec -it shopsmart-db psql -U shopsmart -d shopsmart

# Reset database (WARNING: deletes all data)
docker compose down -v && docker compose up --build
```

## High-Level Architecture

### Three-Tier Recommendation Strategy

The system implements a fallback cascade in `RecommendationService.get_recommendations()`:

1. **Personalized** (if user has interaction history): Item-to-item collaborative filtering
   - Uses last 50 user events weighted by type (view=1, add_to_cart=3, purchase=5)
   - Aggregates similarity scores from precomputed `item_similarity` table
   - Filters out already-interacted products

2. **Cold Start with Category** (if user is new but category specified): Trending by category
   - Falls back when user has no history but requests category-specific recs
   - Uses `trending_scores` table filtered by `category_id`

3. **Global Trending** (fallback): Universal popularity
   - Used for completely new users without context
   - Returns top products from `trending_scores` with time_window='7d'

### Redis Cache Architecture

Cache keys follow a namespace pattern with specific TTLs:

```
rec:{user_id}:{k}:{category_id}    → Recommendations (TTL: 5 min)
sim:{product_id}:{k}                → Similar products (TTL: 1 hour)
trending:{time_window}              → Trending lists (TTL: 15 min)
admin:dashboard                     → Admin stats (TTL: 1 min)
```

**Cache Invalidation Points**:
- `POST /events`: Invalidates `rec:{user_id}:*` for that user
- ML pipeline completion: Invalidates all `sim:*` and `trending:*`
- Admin flush endpoints: Manual invalidation via API

### ML Pipeline Dependencies

**Critical order** - pipelines must run in this sequence:

1. **Data Loading** (run once)
   ```bash
   python -m data.seed.synthetic_generator
   # OR
   python -m data.seed.retailrocket_loader
   ```
   Populates: `categories`, `products`, `users`, `events`

2. **Trending Pipeline** (run periodically, e.g., hourly)
   ```bash
   python -m pipelines.trending_pipeline
   ```
   - Reads: `events`, `products`
   - Writes: `trending_scores` (with time_windows '7d' and '30d')
   - Algorithm: Time-decayed exponential scoring with λ=0.3 (7d) or λ=0.1 (30d)
   - Invalidates: `trending:*` and `rec:*` cache keys

3. **Similarity Pipeline** (run periodically, e.g., daily)
   ```bash
   python -m pipelines.similarity_pipeline
   ```
   - Reads: `events` from last 90 days, `products`
   - Writes: `item_similarity` (top 50 similar products per item)
   - Algorithm: Weighted user-item matrix → cosine similarity → filter by min 2 co-occurrences
   - Processes in batches of 500 products for memory efficiency
   - Invalidates: `sim:*` and `rec:*` cache keys

4. **Evaluation** (optional, for metrics)
   ```bash
   python -m pipelines.evaluation
   ```
   - Temporal split: last 7 days as test set
   - Computes: Recall@K, Precision@K, Hit Rate@K, NDCG@K

### Service Layer Pattern

All business logic lives in `backend/app/services/`:

- **EventService**: User/event CRUD + cache invalidation trigger
- **ProductService**: Product search/retrieval with PostgreSQL full-text search
- **RecommendationService**: Orchestrates strategy selection, delegates to:
  - **TrendingService**: Queries `trending_scores` table
  - **SimilarityService**: Queries `item_similarity` table

Services are instantiated per-request via dependency injection. They receive a `Session` object for database access.

### Event Flow

```
User Action (Frontend)
  → trackView/trackAddToCart (services/tracking.ts)
  → POST /events (api/routes/events.py)
  → EventService.create_event()
  → Inserts into `events` table
  → Invalidates cache_service.invalidate_user_recommendations(user.external_id)
  → Returns event confirmation
```

### Frontend User Identity

The frontend generates persistent IDs stored in browser storage:
- `localStorage.shopsmart_user_id`: Persistent across sessions
- `sessionStorage.shopsmart_session_id`: Per-session tracking

These IDs are sent with every event to the backend, which auto-creates anonymous users in the `users` table.

## Important Non-Obvious Details

### Database Schema Design Choices

- **external_id fields**: Bridge RetailRocket dataset IDs to internal auto-increment IDs
- **is_anonymous flag**: Supports future registered user features without schema changes
- **event metadata JSONB**: Extensible event properties without migrations
- **time_window in trending_scores**: Allows multiple decay rates (7d/30d) simultaneously

### ML Pipeline Batch Processing

`SimilarityPipeline` processes in batches (default 500 products) to avoid memory exhaustion on large datasets. Batch size configurable but affects:
- Memory usage (larger = more RAM needed)
- Progress visibility (smaller = more frequent updates)
- I/O overhead (smaller = more database round-trips)

### Cold Start Strategy Edge Case

If user has interactions but `get_collaborative_recommendations()` returns < k/2 items (low similarity scores), the system falls back to trending rather than returning a sparse recommendation set. This ensures users always see a full page of recommendations.

### PostgreSQL Extensions

`init.sql` requires `pg_trgm` extension for fuzzy product name search. If working with a managed database, ensure this extension is available or disable trigram indexes in `ProductService.search_products()`.

### RetailRocket Dataset Mapping

When loading RetailRocket data:
- `visitorid` → `users.external_id` (prefixed with "RR_")
- `itemid` → `products.external_id` (prefixed with "RR_ITEM_")
- `event` field maps: `view`→`view`, `addtocart`→`add_to_cart`, `transaction`→`purchase`
- `timestamp` is in milliseconds, converted to Python datetime

### Cache Invalidation on Event Creation

Every event triggers `cache_service.invalidate_user_recommendations(user_id)`, which can be expensive for high-traffic users. Consider:
- Rate limiting cache invalidation (e.g., max once per 30 seconds per user)
- Or removing invalidation entirely and relying on TTL expiry (5 min is short enough)

## Troubleshooting

### Empty Recommendations

If recommendations return empty:
1. Check if ML pipelines have run: `SELECT COUNT(*) FROM trending_scores;` should be > 0
2. Check if events exist: `SELECT COUNT(*) FROM events;`
3. Check user has events: `SELECT COUNT(*) FROM events WHERE user_id = (SELECT id FROM users WHERE external_id = 'user123');`

### Slow Similar Products Queries

If `GET /similar-products` is slow:
1. Verify index exists: `\d item_similarity` should show index on `(product_id, similarity_score DESC)`
2. Check similarity table size: Large products × 50 similar = millions of rows
3. Consider reducing `top_k_similar` in similarity pipeline from 50 to 20

### ML Pipeline Out of Memory

If similarity pipeline crashes:
- Reduce `batch_size` in `SimilarityPipeline.__init__()` from 500 to 100
- Reduce `lookback_days` from 90 to 30 (fewer events to process)
- Use synthetic data with fewer products/events instead of full RetailRocket dataset

## Access Points

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs (FastAPI interactive docs)
- Admin Dashboard: http://localhost:3000/admin
- Health Check: http://localhost:8000/health
- PostgreSQL: `localhost:5432` (user: shopsmart, db: shopsmart)
- Redis: `localhost:6379/0`
