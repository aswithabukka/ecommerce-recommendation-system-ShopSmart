import { trackEvent } from './api';
import type { EventCreate, EventType } from '../types';

// Generate or retrieve session ID
const getSessionId = (): string => {
  let sessionId = sessionStorage.getItem('shopsmart_session_id');
  if (!sessionId) {
    sessionId = `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('shopsmart_session_id', sessionId);
  }
  return sessionId;
};

// Get or generate user ID
export const getUserId = (): string => {
  let userId = localStorage.getItem('shopsmart_user_id');
  if (!userId) {
    userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('shopsmart_user_id', userId);
  }
  return userId;
};

// Generic event tracking
const track = async (productId: number, eventType: EventType): Promise<void> => {
  const event: EventCreate = {
    user_id: getUserId(),
    product_id: productId,
    event_type: eventType,
    session_id: getSessionId(),
  };

  try {
    await trackEvent(event);
  } catch (error) {
    console.error(`Failed to track ${eventType} event:`, error);
  }
};

// Track view event
export const trackView = async (productId: number): Promise<void> => {
  await track(productId, 'view');
};

// Track add to cart event
export const trackAddToCart = async (productId: number): Promise<void> => {
  await track(productId, 'add_to_cart');
};

// Track purchase event
export const trackPurchase = async (productId: number): Promise<void> => {
  await track(productId, 'purchase');
};

// Track multiple purchases
export const trackPurchases = async (productIds: number[]): Promise<void> => {
  await Promise.all(productIds.map((id) => track(id, 'purchase')));
};
