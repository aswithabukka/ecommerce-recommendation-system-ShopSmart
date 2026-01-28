-- ShopSmart Database Initialization
-- Extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ===========================================
-- CORE TABLES
-- ===========================================

-- Categories for products
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    parent_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products catalog
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2),
    image_url VARCHAR(1000),
    category_id INTEGER REFERENCES categories(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for products
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON products USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);

-- Users (anonymous and registered)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE,
    is_anonymous BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_external_id ON users(external_id);

-- ===========================================
-- EVENT TRACKING
-- ===========================================

-- User events (view, add_to_cart, purchase)
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('view', 'add_to_cart', 'purchase')),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255),
    metadata JSONB
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_product ON events(product_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_user_product ON events(user_id, product_id);
CREATE INDEX IF NOT EXISTS idx_events_user_timestamp ON events(user_id, timestamp DESC);

-- ===========================================
-- RECOMMENDATION TABLES (ML Pipeline Output)
-- ===========================================

-- Trending scores (refreshed by ML pipeline)
CREATE TABLE IF NOT EXISTS trending_scores (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    category_id INTEGER REFERENCES categories(id),
    time_window VARCHAR(20) NOT NULL CHECK (time_window IN ('7d', '30d')),
    score FLOAT NOT NULL,
    event_count INTEGER NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, time_window)
);

CREATE INDEX IF NOT EXISTS idx_trending_category_window ON trending_scores(category_id, time_window);
CREATE INDEX IF NOT EXISTS idx_trending_score ON trending_scores(time_window, score DESC);

-- Item-to-item similarity (co-occurrence based)
CREATE TABLE IF NOT EXISTS item_similarity (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    similar_product_id INTEGER NOT NULL REFERENCES products(id),
    similarity_score FLOAT NOT NULL,
    co_occurrence_count INTEGER NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, similar_product_id)
);

CREATE INDEX IF NOT EXISTS idx_similarity_product ON item_similarity(product_id);
CREATE INDEX IF NOT EXISTS idx_similarity_score ON item_similarity(product_id, similarity_score DESC);

-- ===========================================
-- ADMIN / ANALYTICS
-- ===========================================

-- Daily event aggregations for admin dashboard
CREATE TABLE IF NOT EXISTS daily_event_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_count INTEGER NOT NULL,
    unique_users INTEGER NOT NULL,
    unique_products INTEGER NOT NULL,
    UNIQUE(date, event_type)
);

CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_event_stats(date DESC);

-- API request stats
CREATE TABLE IF NOT EXISTS api_stats (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    request_count INTEGER DEFAULT 0,
    avg_response_time_ms FLOAT,
    error_count INTEGER DEFAULT 0,
    UNIQUE(endpoint, date)
);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO shopsmart;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO shopsmart;
