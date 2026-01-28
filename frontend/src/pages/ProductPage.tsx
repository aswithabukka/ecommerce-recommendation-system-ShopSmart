import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getProduct } from '../services/api';
import { trackView, trackAddToCart } from '../services/tracking';
import { SimilarProducts } from '../components/SimilarProducts';
import { Loading } from '../components/Loading';
import { useCart } from '../contexts/CartContext';
import type { Product } from '../types';

export const ProductPage: React.FC = () => {
  const { productId } = useParams<{ productId: string }>();
  const { addToCart } = useCart();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addedToCart, setAddedToCart] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      if (!productId) return;

      const id = parseInt(productId, 10);

      try {
        setLoading(true);
        setError(null);

        // Fetch product details
        const productData = await getProduct(id);
        setProduct(productData);

        // Track view event
        await trackView(id);
      } catch (err) {
        setError('Product not found');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // Reset cart state when product changes
    setAddedToCart(false);
  }, [productId]);

  const handleAddToCart = async () => {
    if (product) {
      try {
        // Track the event
        await trackAddToCart(product.id);

        // Add to cart context
        addToCart(product);

        // Show success feedback
        setAddedToCart(true);
        setTimeout(() => setAddedToCart(false), 2000);
      } catch (error) {
        console.error('Failed to add to cart:', error);
      }
    }
  };

  if (loading) return <Loading text="Loading product..." />;
  if (error || !product) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Product Not Found</h1>
        <p className="text-gray-500 mb-8">The product you're looking for doesn't exist.</p>
        <Link
          to="/"
          className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Back to Home
        </Link>
      </div>
    );
  }

  const imageUrl = product.image_url || `https://picsum.photos/seed/${product.id}/600/600`;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm">
        <Link to="/" className="text-blue-600 hover:underline">
          Home
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-600">{product.name}</span>
      </nav>

      {/* Product Details */}
      <div className="grid md:grid-cols-2 gap-8 mb-12">
        <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
          <img
            src={imageUrl}
            alt={product.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.src = `https://via.placeholder.com/600x600?text=${encodeURIComponent(product.name.slice(0, 20))}`;
            }}
          />
        </div>

        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            {product.name}
          </h1>

          {product.price !== undefined && product.price !== null && (
            <p className="text-3xl font-bold text-blue-600 mb-6">
              ${product.price.toFixed(2)}
            </p>
          )}

          {product.description && (
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Description</h2>
              <p className="text-gray-600 leading-relaxed">{product.description}</p>
            </div>
          )}

          <div className="space-y-4">
            <button
              onClick={handleAddToCart}
              className={`w-full md:w-auto px-8 py-3 rounded-lg text-lg font-medium transition-all ${
                addedToCart
                  ? 'bg-green-600 text-white'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {addedToCart ? 'Added to Cart!' : 'Add to Cart'}
            </button>

            <p className="text-sm text-gray-500">
              Product ID: {product.id}
              {product.external_id && ` | SKU: ${product.external_id}`}
            </p>
          </div>
        </div>
      </div>

      {/* Similar Products */}
      <SimilarProducts productId={product.id} count={8} />
    </div>
  );
};
