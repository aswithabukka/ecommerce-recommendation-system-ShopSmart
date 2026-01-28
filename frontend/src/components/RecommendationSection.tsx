import React, { useEffect, useState } from 'react';
import { ProductGrid } from './ProductGrid';
import { Loading } from './Loading';
import { getRecommendations } from '../services/api';
import { getUserId } from '../services/tracking';
import type { ProductWithScore, RecommendationStrategy } from '../types';

interface RecommendationSectionProps {
  title: string;
  categoryId?: number;
  count?: number;
}

const strategyLabels: Record<RecommendationStrategy, string> = {
  personalized: 'Based on your activity',
  trending: 'Popular now',
  cold_start_category: 'Trending in category',
};

export const RecommendationSection: React.FC<RecommendationSectionProps> = ({
  title,
  categoryId,
  count = 8,
}) => {
  const [products, setProducts] = useState<ProductWithScore[]>([]);
  const [strategy, setStrategy] = useState<RecommendationStrategy>('trending');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        setLoading(true);
        setError(null);
        const userId = getUserId();
        const response = await getRecommendations(userId, count, categoryId);
        setProducts(response.recommendations);
        setStrategy(response.strategy);
      } catch (err) {
        setError('Failed to load recommendations');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [categoryId, count]);

  if (loading) return <Loading text="Loading recommendations..." />;
  if (error) return <div className="text-red-500 text-center py-8">{error}</div>;
  if (products.length === 0) return null;

  return (
    <section className="mb-10">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
        <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
          {strategyLabels[strategy]}
        </span>
      </div>
      <ProductGrid products={products} showScore={false} />
    </section>
  );
};
