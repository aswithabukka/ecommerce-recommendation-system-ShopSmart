import React, { useEffect, useState } from 'react';
import { ProductGrid } from './ProductGrid';
import { Loading } from './Loading';
import { getSimilarProducts } from '../services/api';
import type { ProductWithScore } from '../types';

interface SimilarProductsProps {
  productId: number;
  count?: number;
}

export const SimilarProducts: React.FC<SimilarProductsProps> = ({
  productId,
  count = 8,
}) => {
  const [products, setProducts] = useState<ProductWithScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSimilar = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await getSimilarProducts(productId, count);
        setProducts(response.similar_products);
      } catch (err) {
        setError('Failed to load similar products');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchSimilar();
  }, [productId, count]);

  if (loading) return <Loading text="Loading similar products..." />;
  if (error) return null; // Silently fail for similar products
  if (products.length === 0) return null;

  return (
    <section className="mt-12">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Similar Products</h2>
      <ProductGrid products={products} showScore={false} />
    </section>
  );
};
