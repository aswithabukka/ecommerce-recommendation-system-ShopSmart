import axios from 'axios';
import type {
  Product,
  EventCreate,
  RecommendationResponse,
  SimilarProductsResponse,
  ProductSearchResponse,
  AdminDashboard,
  HealthResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// Events API
export const trackEvent = async (event: EventCreate): Promise<void> => {
  await api.post('/events', event);
};

// Recommendations API
export const getRecommendations = async (
  userId: string,
  k: number = 10,
  categoryId?: number
): Promise<RecommendationResponse> => {
  const params: Record<string, unknown> = { user_id: userId, k };
  if (categoryId) params.category_id = categoryId;
  const response = await api.get('/recommendations', { params });
  return response.data;
};

export const getSimilarProducts = async (
  productId: number,
  k: number = 10
): Promise<SimilarProductsResponse> => {
  const response = await api.get('/similar-products', {
    params: { product_id: productId, k },
  });
  return response.data;
};

// Products API
export const searchProducts = async (
  search?: string,
  category?: string,
  page: number = 1,
  pageSize: number = 20
): Promise<ProductSearchResponse> => {
  const params: Record<string, unknown> = { page, page_size: pageSize };
  if (search) params.search = search;
  if (category) params.category = category;
  const response = await api.get('/products', { params });
  return response.data;
};

export const getProduct = async (productId: number): Promise<Product> => {
  const response = await api.get(`/products/${productId}`);
  return response.data;
};

// Admin API
export const getAdminDashboard = async (): Promise<AdminDashboard> => {
  const response = await api.get('/admin/dashboard');
  return response.data;
};

export const flushCache = async (type?: string): Promise<{ message: string }> => {
  const endpoint = type ? `/admin/cache/flush/${type}` : '/admin/cache/flush';
  const response = await api.post(endpoint);
  return response.data;
};

// Health check
export const healthCheck = async (): Promise<HealthResponse> => {
  const response = await api.get('/health');
  return response.data;
};

// Export the axios instance for direct use
export { api };
