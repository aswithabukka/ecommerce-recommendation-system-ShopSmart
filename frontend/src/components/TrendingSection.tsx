import React, { useEffect, useState } from 'react';
import { ProductCard } from './ProductCard';
import { Loading } from './Loading';
import { getRecommendations } from '../services/api';
import type { ProductWithScore } from '../types';

interface TrendingSectionProps {
  count?: number;
}

export const TrendingSection: React.FC<TrendingSectionProps> = ({ count = 8 }) => {
  const [products, setProducts] = useState<ProductWithScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTrending = async () => {
      try {
        setLoading(true);
        setError(null);
        // Use a generic user ID to get trending (cold start behavior)
        const response = await getRecommendations('trending_guest', count);
        setProducts(response.recommendations);
      } catch (err) {
        setError('Failed to load trending products');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchTrending();
  }, [count]);

  if (loading) return <Loading text="Loading trending products..." />;
  if (error) return <div className="text-red-500 text-center py-8">{error}</div>;
  if (products.length === 0) return null;

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Trending Now</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {products.map((product, index) => (
          <div key={product.id} className="relative">
            <div className="absolute top-2 left-2 bg-orange-500 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold z-10 shadow-md">
              {index + 1}
            </div>
            <ProductCard product={product} />
          </div>
        ))}
      </div>
    </section>
  );
};
