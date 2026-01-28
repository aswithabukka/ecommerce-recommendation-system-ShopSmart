import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import type { Product, ProductWithScore } from '../types';
import { trackAddToCart } from '../services/tracking';
import { useCart } from '../contexts/CartContext';

interface ProductCardProps {
  product: Product | ProductWithScore;
  showScore?: boolean;
  onAddToCart?: (productId: number) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  showScore = false,
  onAddToCart,
}) => {
  const hasScore = 'score' in product && product.score !== undefined;
  const { addToCart } = useCart();
  const [addedToCart, setAddedToCart] = useState(false);

  const handleAddToCart = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    try {
      await trackAddToCart(product.id);
      addToCart(product);
      setAddedToCart(true);

      // Reset the "added" state after 2 seconds
      setTimeout(() => setAddedToCart(false), 2000);

      if (onAddToCart) {
        onAddToCart(product.id);
      }
    } catch (error) {
      console.error('Failed to add to cart:', error);
    }
  };

  // Generate a placeholder image URL based on product ID
  const imageUrl = product.image_url || `https://picsum.photos/seed/${product.id}/400/400`;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow group">
      <Link to={`/product/${product.id}`}>
        <div className="aspect-square bg-gray-100 relative overflow-hidden">
          <img
            src={imageUrl}
            alt={product.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.src = `https://via.placeholder.com/400x400?text=${encodeURIComponent(product.name.slice(0, 20))}`;
            }}
          />
          {showScore && hasScore && (
            <div className="absolute top-2 right-2 bg-blue-600 text-white px-2 py-1 rounded-full text-xs font-semibold">
              {(product as ProductWithScore).score?.toFixed(1)}
            </div>
          )}
        </div>
      </Link>

      <div className="p-4">
        <Link to={`/product/${product.id}`}>
          <h3 className="font-medium text-gray-900 line-clamp-2 hover:text-blue-600 transition-colors">
            {product.name}
          </h3>
        </Link>

        {product.average_rating !== undefined && product.average_rating > 0 && (
          <div className="mt-2 flex items-center space-x-1">
            {Array.from({ length: 5 }).map((_, i) => (
              <span
                key={i}
                className={i < Math.floor(product.average_rating || 0) ? 'text-yellow-500' : 'text-gray-300'}
              >
                ★
              </span>
            ))}
            <span className="text-sm text-gray-600 ml-1">
              ({product.review_count || 0})
            </span>
          </div>
        )}

        {product.price !== undefined && product.price !== null && (
          <p className="mt-2 text-lg font-semibold text-gray-900">
            ${product.price.toFixed(2)}
          </p>
        )}

        <button
          onClick={handleAddToCart}
          className={`mt-3 w-full py-2 px-4 rounded-md transition-all text-sm font-medium ${
            addedToCart
              ? 'bg-green-600 text-white'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
          disabled={addedToCart}
        >
          {addedToCart ? '✓ Added to Cart!' : 'Add to Cart'}
        </button>
      </div>
    </div>
  );
};
