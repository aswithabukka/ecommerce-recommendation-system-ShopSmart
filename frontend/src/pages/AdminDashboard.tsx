import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getAdminDashboard, flushCache } from '../services/api';
import { Loading } from '../components/Loading';
import type { AdminDashboard as AdminDashboardType, DailyEventStats, TrendingProduct } from '../types';

export const AdminDashboard: React.FC = () => {
  const [data, setData] = useState<AdminDashboardType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [flushMessage, setFlushMessage] = useState<string | null>(null);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const dashboardData = await getAdminDashboard();
      setData(dashboardData);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleFlushCache = async (type?: string) => {
    try {
      const result = await flushCache(type);
      setFlushMessage(result.message);
      setTimeout(() => setFlushMessage(null), 3000);
      // Refresh dashboard after flush
      await fetchDashboard();
    } catch (err) {
      console.error('Failed to flush cache:', err);
      setFlushMessage('Failed to flush cache');
      setTimeout(() => setFlushMessage(null), 3000);
    }
  };

  // Group events by day
  const groupEventsByDay = (events: DailyEventStats[]): Record<string, Record<string, number>> => {
    const grouped: Record<string, Record<string, number>> = {};
    events.forEach((stat) => {
      const date = stat.date.split('T')[0];
      if (!grouped[date]) {
        grouped[date] = { view: 0, add_to_cart: 0, purchase: 0 };
      }
      grouped[date][stat.event_type] = stat.event_count;
    });
    return grouped;
  };

  if (loading) return <Loading text="Loading dashboard..." />;
  if (error || !data) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 text-center">
        <p className="text-red-500 mb-4">{error || 'Failed to load dashboard'}</p>
        <button
          onClick={fetchDashboard}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const eventsByDay = groupEventsByDay(data.events_by_day);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm">
        <Link to="/" className="text-blue-600 hover:underline">
          Home
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-600">Admin Dashboard</span>
      </nav>

      <h1 className="text-3xl font-bold text-gray-900 mb-8">Admin Dashboard</h1>

      {/* Flash Message */}
      {flushMessage && (
        <div className="mb-6 p-4 bg-green-100 text-green-700 rounded-lg">
          {flushMessage}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
            Total Events
          </h3>
          <p className="text-4xl font-bold text-gray-900 mt-2">
            {data.total_events.toLocaleString()}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
            Total Users
          </h3>
          <p className="text-4xl font-bold text-gray-900 mt-2">
            {data.total_users.toLocaleString()}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
            Total Products
          </h3>
          <p className="text-4xl font-bold text-gray-900 mt-2">
            {data.total_products.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Cache Management */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Cache Management</h2>
        </div>
        <div className="p-6 flex flex-wrap gap-3">
          <button
            onClick={() => handleFlushCache()}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Flush All Cache
          </button>
          <button
            onClick={() => handleFlushCache('recommendations')}
            className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
          >
            Flush Recommendations
          </button>
          <button
            onClick={() => handleFlushCache('similar')}
            className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
          >
            Flush Similar Products
          </button>
          <button
            onClick={() => handleFlushCache('trending')}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            Flush Trending
          </button>
        </div>
      </div>

      {/* Events by Day Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Events by Day (Last 7 Days)</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Views
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Add to Cart
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Purchases
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {Object.entries(eventsByDay)
                .sort(([a], [b]) => b.localeCompare(a))
                .slice(0, 7)
                .map(([date, counts]) => (
                  <tr key={date} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {(counts.view || 0).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {(counts.add_to_cart || 0).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {(counts.purchase || 0).toLocaleString()}
                    </td>
                  </tr>
                ))}
              {Object.keys(eventsByDay).length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                    No events recorded yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top Trending Products */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Top Trending Products</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rank
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Product
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Events
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data.top_trending.map((item: TrendingProduct, index: number) => (
                <tr key={item.product.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full font-semibold text-sm">
                      {index + 1}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <Link
                      to={`/product/${item.product.id}`}
                      className="text-blue-600 hover:underline font-medium"
                    >
                      {item.product.name}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {item.score.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {item.event_count.toLocaleString()}
                  </td>
                </tr>
              ))}
              {data.top_trending.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                    No trending data available. Run the ML pipeline to generate trending scores.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
