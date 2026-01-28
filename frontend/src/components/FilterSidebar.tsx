import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

interface FilterSidebarProps {
  onFilterChange: (filters: {
    category?: string;
    minPrice?: number;
    maxPrice?: number;
    minRating?: number;
  }) => void;
  currentFilters: {
    category?: string;
    minPrice?: number;
    maxPrice?: number;
    minRating?: number;
  };
}

interface Category {
  id: number;
  name: string;
  product_count: number;
}

const FilterSidebar: React.FC<FilterSidebarProps> = ({ onFilterChange, currentFilters }) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [minPrice, setMinPrice] = useState(currentFilters.minPrice?.toString() || '');
  const [maxPrice, setMaxPrice] = useState(currentFilters.maxPrice?.toString() || '');

  useEffect(() => {
    api.get('/products/categories')
      .then(res => setCategories(res.data))
      .catch(err => console.error('Failed to load categories:', err));
  }, []);

  const handleCategoryClick = (categoryName: string) => {
    const newCategory = currentFilters.category === categoryName ? undefined : categoryName;
    onFilterChange({ ...currentFilters, category: newCategory });
  };

  const handlePriceChange = () => {
    onFilterChange({
      ...currentFilters,
      minPrice: minPrice ? parseFloat(minPrice) : undefined,
      maxPrice: maxPrice ? parseFloat(maxPrice) : undefined
    });
  };

  const handleRatingClick = (rating: number) => {
    const newRating = currentFilters.minRating === rating ? undefined : rating;
    onFilterChange({ ...currentFilters, minRating: newRating });
  };

  const clearFilters = () => {
    setMinPrice('');
    setMaxPrice('');
    onFilterChange({});
  };

  return (
    <div className="w-64 bg-white rounded-lg shadow p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-lg">Filters</h3>
        <button
          onClick={clearFilters}
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          Clear All
        </button>
      </div>

      {/* Categories */}
      <div>
        <h4 className="font-medium mb-3">Categories</h4>
        <div className="space-y-2">
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => handleCategoryClick(cat.name)}
              className={`w-full text-left px-3 py-2 rounded transition ${
                currentFilters.category === cat.name
                  ? 'bg-blue-100 text-blue-700 font-medium'
                  : 'hover:bg-gray-100'
              }`}
            >
              <div className="flex justify-between items-center">
                <span>{cat.name}</span>
                <span className="text-sm text-gray-500">{cat.product_count}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Price Range */}
      <div>
        <h4 className="font-medium mb-3">Price Range</h4>
        <div className="space-y-2">
          <input
            type="number"
            placeholder="Min"
            value={minPrice}
            onChange={(e) => setMinPrice(e.target.value)}
            className="w-full px-3 py-2 border rounded"
          />
          <input
            type="number"
            placeholder="Max"
            value={maxPrice}
            onChange={(e) => setMaxPrice(e.target.value)}
            className="w-full px-3 py-2 border rounded"
          />
          <button
            onClick={handlePriceChange}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
          >
            Apply
          </button>
        </div>
      </div>

      {/* Rating Filter */}
      <div>
        <h4 className="font-medium mb-3">Minimum Rating</h4>
        <div className="space-y-2">
          {[5, 4, 3, 2, 1].map(rating => (
            <button
              key={rating}
              onClick={() => handleRatingClick(rating)}
              className={`w-full text-left px-3 py-2 rounded transition ${
                currentFilters.minRating === rating
                  ? 'bg-blue-100 text-blue-700 font-medium'
                  : 'hover:bg-gray-100'
              }`}
            >
              <div className="flex items-center space-x-1">
                {Array.from({ length: rating }).map((_, i) => (
                  <span key={i} className="text-yellow-500">★</span>
                ))}
                {Array.from({ length: 5 - rating }).map((_, i) => (
                  <span key={i} className="text-gray-300">★</span>
                ))}
                <span className="ml-2">& Up</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FilterSidebar;
