import React from 'react';
import { ProductCard } from './ProductCard';
import type { Product, ProductWithScore } from '../types';

interface ProductGridProps {
  products: (Product | ProductWithScore)[];
  showScore?: boolean;
  onAddToCart?: (productId: number) => void;
}

export const ProductGrid: React.FC<ProductGridProps> = ({
  products,
  showScore = false,
  onAddToCart,
}) => {
  if (products.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No products found
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {products.map((product) => (
        <ProductCard
          key={product.id}
          product={product}
          showScore={showScore}
          onAddToCart={onAddToCart}
        />
      ))}
    </div>
  );
};
