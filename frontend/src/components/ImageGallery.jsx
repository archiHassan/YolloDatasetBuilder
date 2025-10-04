import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getImages, getImageUrl } from '../api/client';

function ImageGallery() {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const limit = 20;

  // Filter and search states
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('newest');

  useEffect(() => {
    fetchImages();
  }, [page, statusFilter, sortBy]);

  // Reset to page 0 when filters change
  useEffect(() => {
    if (page !== 0) {
      setPage(0);
    }
  }, [searchQuery, statusFilter, sortBy]);

  const fetchImages = async () => {
    try {
      setLoading(true);
      const data = await getImages(page * limit, limit);
      setImages(data.images);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError('Failed to load images: ' + err.message);
      console.error('Error fetching images:', err);
    } finally {
      setLoading(false);
    }
  };

  // Filter and sort images on client side
  const getFilteredAndSortedImages = () => {
    let filtered = [...images];

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(img =>
        img.filename.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(img => img.status === statusFilter);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return b.id - a.id;
        case 'oldest':
          return a.id - b.id;
        case 'name-asc':
          return a.filename.localeCompare(b.filename);
        case 'name-desc':
          return b.filename.localeCompare(a.filename);
        case 'size-asc':
          return a.size - b.size;
        case 'size-desc':
          return b.size - a.size;
        default:
          return 0;
      }
    });

    return filtered;
  };

  const filteredImages = getFilteredAndSortedImages();

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading images...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
        <button
          onClick={fetchImages}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8">
      <div className="container mx-auto px-6 max-w-[1400px]">
        {/* Header - More Prominent */}
        <div className="mb-8 bg-white rounded-2xl shadow-lg p-6 border-l-4 border-blue-600">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">📸 Image Gallery</h2>
            <div className="flex items-center gap-4 text-sm">
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full font-semibold">
                {filteredImages.length} / {total} images
              </span>
              <span className="text-gray-600">
                Page {page + 1} of {Math.ceil(total / limit)}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-xs text-gray-500">Quick Actions</p>
              <Link
                to="/review"
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Go to Review →
              </Link>
            </div>
          </div>
        </div>
      </div>

        {/* Search and Filters - Enhanced */}
        <div className="mb-8 bg-white rounded-2xl shadow-lg p-6 border-t-4 border-blue-400">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-800 mb-1">🔍 Search & Filter</h3>
          <p className="text-xs text-gray-500">Find images quickly using search and filters</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search Bar - Enhanced */}
          <div className="relative">
            <label className="block text-xs font-medium text-gray-700 mb-1">Search by filename</label>
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none" style={{ top: '24px' }}>
              <svg className="h-5 w-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              placeholder="Type to search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="block w-full pl-10 pr-10 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm font-medium shadow-sm hover:border-blue-300 transition-colors"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 text-gray-400 hover:text-red-600 transition-colors"
                style={{ top: '32px' }}
                title="Clear search"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* Status Filter - Enhanced */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Filter by status</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                </svg>
              </div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="block w-full pl-10 pr-3 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm font-medium shadow-sm hover:border-blue-300 transition-colors appearance-none bg-white"
              >
                <option value="all">🔵 All Status</option>
                <option value="pending">🟡 Pending</option>
                <option value="approved">🟢 Approved</option>
                <option value="rejected">🔴 Rejected</option>
              </select>
            </div>
          </div>

          {/* Sort By - Enhanced */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Sort by</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
                </svg>
              </div>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="block w-full pl-10 pr-3 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm font-medium shadow-sm hover:border-blue-300 transition-colors appearance-none bg-white"
              >
                <option value="newest">⬇️ Newest First</option>
                <option value="oldest">⬆️ Oldest First</option>
                <option value="name-asc">🔤 Name (A-Z)</option>
                <option value="name-desc">🔤 Name (Z-A)</option>
                <option value="size-asc">📊 Size (Small to Large)</option>
                <option value="size-desc">📊 Size (Large to Small)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Active Filters Display */}
        {(searchQuery || statusFilter !== 'all') && (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-xs text-gray-600">Active filters:</span>
            {searchQuery && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Search: "{searchQuery}"
                <button
                  onClick={() => setSearchQuery('')}
                  className="ml-1 hover:text-blue-900"
                >
                  ×
                </button>
              </span>
            )}
            {statusFilter !== 'all' && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Status: {statusFilter}
                <button
                  onClick={() => setStatusFilter('all')}
                  className="ml-1 hover:text-green-900"
                >
                  ×
                </button>
              </span>
            )}
            <button
              onClick={() => {
                setSearchQuery('');
                setStatusFilter('all');
              }}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
            >
              Clear all
            </button>
          </div>
        )}
      </div>

        {/* No Results Message */}
        {filteredImages.length === 0 && (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No images found</h3>
          <p className="mt-1 text-sm text-gray-500">Try adjusting your search or filters</p>
          <button
            onClick={() => {
              setSearchQuery('');
              setStatusFilter('all');
            }}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
          >
            Clear filters
          </button>
        </div>
      )}

        {/* Gallery Grid - Enhanced Visibility */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {filteredImages.map((image) => (
          <Link
            key={image.id}
            to={`/image/${image.id}`}
            className="group relative bg-white rounded-2xl shadow-xl overflow-hidden hover:shadow-2xl hover:scale-[1.03] hover:-translate-y-2 transition-all duration-300 border-2 border-transparent hover:border-blue-400"
          >
            {/* Image Container with fixed height */}
            <div className="relative h-48 bg-gradient-to-br from-gray-100 to-gray-200 overflow-hidden">
              <img
                src={getImageUrl(image.filename)}
                alt={image.filename}
                className="w-full h-full object-contain group-hover:scale-110 transition-transform duration-500"
                onError={(e) => {
                  e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23ddd" width="100" height="100"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle"%3ENo Image%3C/text%3E%3C/svg%3E';
                }}
              />
              {/* Status Badge Overlay - More Prominent */}
              <div className="absolute top-4 right-4">
                <span className={`px-4 py-2 rounded-full text-sm font-bold shadow-2xl backdrop-blur-sm ${
                  image.status === 'pending'
                    ? 'bg-yellow-400 text-yellow-900 ring-2 ring-yellow-300'
                    : image.status === 'approved'
                    ? 'bg-green-500 text-white ring-2 ring-green-400'
                    : 'bg-red-500 text-white ring-2 ring-red-400'
                }`}>
                  {image.status === 'pending' ? '🟡' : image.status === 'approved' ? '✅' : '❌'} {image.status.toUpperCase()}
                </span>
              </div>

              {/* Hover Overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <div className="absolute bottom-4 left-4 right-4">
                  <button className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-sm shadow-lg transform translate-y-4 group-hover:translate-y-0 transition-transform duration-300">
                    👁️ View & Edit Image
                  </button>
                </div>
              </div>
            </div>

            {/* Info Section - More prominent and detailed */}
            <div className="p-4 bg-gradient-to-br from-gray-50 via-white to-gray-50">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <p className="text-base font-bold text-gray-900 truncate mb-1" title={image.filename}>
                    📄 {image.filename}
                  </p>
                  <p className="text-xs text-gray-500">ID: #{image.id}</p>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-gray-200">
                <div className="flex items-center space-x-2 bg-blue-50 px-3 py-2 rounded-lg">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span className="text-sm font-bold text-blue-700">
                    {(image.size / 1024).toFixed(1)} KB
                  </span>
                </div>
                <div className="flex items-center text-blue-600 font-semibold group-hover:text-blue-700">
                  <span className="text-sm mr-1">Open</span>
                  <svg className="w-5 h-5 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

        {/* Pagination - Enhanced */}
        {total > limit && (
          <div className="mt-10 flex justify-center items-center gap-3">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-6 py-3 bg-white border-2 border-gray-300 rounded-xl text-sm font-bold text-gray-700 hover:bg-blue-50 hover:border-blue-400 disabled:opacity-40 disabled:cursor-not-allowed shadow-md transition-all"
          >
            ← Previous
          </button>
          <div className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl text-sm font-bold shadow-lg">
            Page {page + 1} of {Math.ceil(total / limit)}
          </div>
          <button
            onClick={() => setPage(Math.min(Math.ceil(total / limit) - 1, page + 1))}
            disabled={page >= Math.ceil(total / limit) - 1}
            className="px-6 py-3 bg-white border-2 border-gray-300 rounded-xl text-sm font-bold text-gray-700 hover:bg-blue-50 hover:border-blue-400 disabled:opacity-40 disabled:cursor-not-allowed shadow-md transition-all"
          >
            Next →
          </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ImageGallery;
