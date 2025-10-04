import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getReviewQueue, approveImage, rejectImage, getImageUrl } from '../api/client';

function ReviewQueue() {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchQueue();
  }, []);

  const fetchQueue = async () => {
    try {
      setLoading(true);
      const data = await getReviewQueue(10);
      setQueue(data.images || []);
      setError(null);
    } catch (err) {
      setError('Failed to load review queue: ' + err.message);
      console.error('Error fetching review queue:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (imageId) => {
    try {
      await approveImage(imageId);
      setQueue(queue.filter((item) => item.image_id !== imageId));
    } catch (err) {
      setError('Failed to approve image: ' + err.message);
    }
  };

  const handleReject = async (imageId) => {
    try {
      const reason = prompt('Enter rejection reason (optional):');
      await rejectImage(imageId, reason || '');
      setQueue(queue.filter((item) => item.image_id !== imageId));
    } catch (err) {
      setError('Failed to reject image: ' + err.message);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading review queue...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
        <button
          onClick={fetchQueue}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Review Queue</h2>
          <p className="mt-1 text-sm text-gray-600">
            {queue.length} images pending review
          </p>
        </div>
        <button
          onClick={fetchQueue}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Refresh Queue
        </button>
      </div>

      {queue.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <p className="text-gray-500 text-lg">No images in review queue</p>
          <Link
            to="/"
            className="mt-4 inline-block px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Go to Gallery
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {queue.map((item) => (
            <div
              key={item.image_id}
              className="bg-white rounded-lg shadow-md overflow-hidden"
            >
              <div className="aspect-square bg-gray-200 relative">
                <Link to={`/image/${item.image_id}`}>
                  <img
                    src={getImageUrl(`${item.image_id}_0.jpg`)}
                    alt={`Image ${item.image_id}`}
                    className="w-full h-full object-cover hover:opacity-90 transition-opacity"
                    onError={(e) => {
                      e.target.src =
                        'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23ddd" width="100" height="100"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle"%3ENo Image%3C/text%3E%3C/svg%3E';
                    }}
                  />
                </Link>
                <span className="absolute top-2 right-2 px-2 py-1 bg-yellow-500 text-white text-xs font-semibold rounded">
                  {item.status}
                </span>
              </div>

              <div className="p-4">
                <p className="text-sm font-medium text-gray-900 mb-3">
                  Image ID: {item.image_id}
                </p>

                <div className="flex space-x-2">
                  <button
                    onClick={() => handleApprove(item.image_id)}
                    className="flex-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                  >
                    ✓ Approve
                  </button>
                  <button
                    onClick={() => handleReject(item.image_id)}
                    className="flex-1 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                  >
                    ✗ Reject
                  </button>
                </div>

                <Link
                  to={`/image/${item.image_id}`}
                  className="mt-2 block text-center text-sm text-blue-600 hover:text-blue-800"
                >
                  View Details →
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ReviewQueue;
