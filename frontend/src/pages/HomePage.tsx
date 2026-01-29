import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { RecommendationSection } from '../components/RecommendationSection';
import { TrendingSection } from '../components/TrendingSection';
import { api } from '../services/api';
import type { Product } from '../types';

interface Category {
  id: number;
  name: string;
  product_count: number;
}

export const HomePage: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [featuredProducts, setFeaturedProducts] = useState<Product[]>([]);

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const response = await api.get('/products/categories');
        setCategories(response.data.slice(0, 8)); // Show top 8 categories
      } catch (error) {
        console.error('Failed to load categories:', error);
      }
    };

    const loadFeaturedProducts = async () => {
      try {
        const response = await api.get('/products/?page_size=12');
        setFeaturedProducts(response.data.products);
      } catch (error) {
        console.error('Failed to load featured products:', error);
      }
    };

    loadCategories();
    loadFeaturedProducts();
  }, []);

  // Map categories to colors for the circular badges
  const categoryColors = [
    'bg-orange-100',
    'bg-green-100',
    'bg-pink-100',
    'bg-red-100',
    'bg-yellow-100',
    'bg-purple-100',
    'bg-blue-100',
    'bg-indigo-100',
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-orange-50 to-orange-100 py-12 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-3xl md:text-4xl font-semibold text-gray-800 mb-3">
            Because everyone deserves something as unique as they are.
          </h1>
          <p className="text-lg text-gray-600 mb-8">Shop special finds</p>

          {/* Category Circles */}
          <div className="flex flex-wrap justify-center gap-6 mt-8">
            {categories.map((category, index) => (
              <Link
                key={category.id}
                to={`/search?category=${encodeURIComponent(category.name)}`}
                className="flex flex-col items-center group"
              >
                <div
                  className={`w-24 h-24 rounded-full ${
                    categoryColors[index % categoryColors.length]
                  } flex items-center justify-center mb-2 group-hover:scale-105 transition-transform shadow-md`}
                >
                  <span className="text-3xl">
                    {getCategoryEmoji(category.name)}
                  </span>
                </div>
                <span className="text-sm font-medium text-gray-700 group-hover:text-blue-600">
                  {category.name}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Personalized Recommendations */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <RecommendationSection
          title="Recommended for You"
          count={8}
        />
      </div>

      {/* Trending Products */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <TrendingSection count={8} />
      </div>

      {/* Browse by Category */}
      <div className="bg-white py-12">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">
            Shop by Category
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {categories.map((category) => (
              <Link
                key={category.id}
                to={`/search?category=${encodeURIComponent(category.name)}`}
                className="bg-gray-50 hover:bg-gray-100 rounded-lg p-6 text-center transition-colors border border-gray-200"
              >
                <div className="text-4xl mb-2">{getCategoryEmoji(category.name)}</div>
                <h3 className="font-medium text-gray-900">{category.name}</h3>
                <p className="text-sm text-gray-500 mt-1">
                  {category.product_count} products
                </p>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Featured Collection */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-gray-900">
            Featured Products
          </h2>
          <Link
            to="/search"
            className="text-blue-600 hover:text-blue-700 font-medium text-sm"
          >
            View all →
          </Link>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
          {featuredProducts.map((product) => (
            <Link
              key={product.id}
              to={`/product/${product.id}`}
              className="group"
            >
              <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden mb-2">
                <img
                  src={product.image_url}
                  alt={product.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  loading="lazy"
                />
              </div>
              <h3 className="text-sm font-medium text-gray-900 line-clamp-2 group-hover:text-blue-600">
                {product.name}
              </h3>
              <p className="text-sm font-semibold text-gray-900 mt-1">
                ${product.price?.toFixed(2) ?? '0.00'}
              </p>
            </Link>
          ))}
        </div>
      </div>

      {/* Call to Action */}
      <div className="bg-blue-600 text-white py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">
            Discover Your Perfect Products
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join thousands of happy shoppers finding exactly what they need
          </p>
          <Link
            to="/search"
            className="inline-block bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
          >
            Start Shopping
          </Link>
        </div>
      </div>
    </div>
  );
};

// Helper function to get emoji based on category name
function getCategoryEmoji(categoryName: string): string {
  const emojiMap: { [key: string]: string } = {
    electronics: '📱',
    clothing: '👕',
    'home & garden': '🏡',
    sports: '⚽',
    books: '📚',
    toys: '🧸',
    beauty: '💄',
    food: '🍕',
  };

  const normalized = categoryName.toLowerCase();
  return emojiMap[normalized] || '🛍️';
}
