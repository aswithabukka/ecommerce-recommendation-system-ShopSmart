// Product types
export interface Product {
  id: number;
  external_id?: string;
  name: string;
  description?: string;
  price?: number;
  image_url?: string;
  category_id?: number;
  is_active: boolean;
  average_rating?: number;
  review_count?: number;
  created_at: string;
}

export interface ProductWithScore extends Product {
  score?: number;
  rank?: number;
}

// Event types
export type EventType = 'view' | 'add_to_cart' | 'purchase';

export interface EventCreate {
  user_id: string;
  product_id: number;
  event_type: EventType;
  timestamp?: string;
  session_id?: string;
  metadata?: Record<string, unknown>;
}

export interface EventResponse {
  id: number;
  user_id: number;
  product_id: number;
  event_type: string;
  timestamp: string;
}

// Recommendation types
export type RecommendationStrategy = 'personalized' | 'trending' | 'cold_start_category';

export interface RecommendationResponse {
  user_id: string;
  recommendations: ProductWithScore[];
  strategy: RecommendationStrategy;
  generated_at: string;
}

export interface SimilarProductsResponse {
  product_id: number;
  similar_products: ProductWithScore[];
  generated_at: string;
}

// Search types
export interface ProductSearchResponse {
  products: Product[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Admin types
export interface DailyEventStats {
  date: string;
  event_type: string;
  event_count: number;
  unique_users: number;
  unique_products: number;
}

export interface TrendingProduct {
  product: Product;
  score: number;
  event_count: number;
  time_window: string;
}

export interface AdminDashboard {
  events_by_day: DailyEventStats[];
  top_trending: TrendingProduct[];
  api_stats: Record<string, unknown>;
  total_events: number;
  total_users: number;
  total_products: number;
}

// Health types
export interface HealthResponse {
  status: string;
  database: string;
  redis: string;
  timestamp: string;
}
