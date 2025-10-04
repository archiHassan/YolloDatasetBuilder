import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getImage, getImageUrl, getAnnotations } from '../api/client';
import ZoomableImage from './ZoomableImage';
import AnnotationEditorV2 from './AnnotationEditorV2';

function ImageViewer() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [image, setImage] = useState(null);
  const [annotations, setAnnotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  useEffect(() => {
    fetchImageData();
  }, [id]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't trigger if user is typing in an input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
      }

      const currentId = parseInt(id);

      switch (e.key) {
        case 'ArrowLeft':
        case 'a':
          // Previous image
          if (currentId > 1) {
            navigate(`/image/${currentId - 1}`);
          }
          break;
        case 'ArrowRight':
        case 'd':
          // Next image
          navigate(`/image/${currentId + 1}`);
          break;
        case 'e':
          // Toggle edit mode
          e.preventDefault();
          setEditMode(!editMode);
          break;
        case 'Escape':
          // Exit edit mode or go back to gallery
          if (editMode) {
            setEditMode(false);
          } else {
            navigate('/');
          }
          break;
        case 'h':
          // Go home
          navigate('/');
          break;
        case '?':
          // Toggle help
          e.preventDefault();
          setShowHelp(!showHelp);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [id, editMode, navigate]);

  const fetchImageData = async () => {
    try {
      setLoading(true);
      const [imageData, annotationsData] = await Promise.all([
        getImage(id),
        getAnnotations(id),
      ]);
      setImage(imageData);
      setAnnotations(annotationsData.annotations || []);
      setError(null);
    } catch (err) {
      setError('Failed to load image: ' + err.message);
      console.error('Error fetching image:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading image...</div>
      </div>
    );
  }

  if (error || !image) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error || 'Image not found'}</p>
        <Link to="/" className="mt-2 inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          Back to Gallery
        </Link>
      </div>
    );
  }

  const handleAnnotationsChange = (newAnnotations) => {
    setAnnotations(newAnnotations);
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-8 bg-white rounded-2xl shadow-lg p-6 border-l-4 border-blue-600">
        <div className="flex justify-between items-center flex-wrap gap-4">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">{image.filename}</h2>
            <div className="flex items-center gap-4 text-sm">
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full font-semibold">
                📦 {(image.size / 1024).toFixed(1)} KB
              </span>
              <span className={`px-3 py-1 rounded-full font-semibold ${
                image.status === 'pending'
                  ? 'bg-yellow-100 text-yellow-800'
                  : image.status === 'approved'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}>
                {image.status === 'pending' ? '🟡' : image.status === 'approved' ? '✅' : '❌'} {image.status.toUpperCase()}
              </span>
            </div>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setShowHelp(!showHelp)}
              className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-xl hover:from-purple-700 hover:to-purple-800 font-semibold shadow-lg hover:shadow-xl transition-all duration-200"
              title="Keyboard Shortcuts (Press ?)"
            >
              <svg className="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Help
            </button>
            <button
              onClick={() => setEditMode(!editMode)}
              className={`px-5 py-2.5 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-200 ${
                editMode
                  ? 'bg-gradient-to-r from-orange-600 to-orange-700 text-white hover:from-orange-700 hover:to-orange-800'
                  : 'bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800'
              }`}
            >
              {editMode ? '👁 View Mode' : '✏️ Edit Mode'}
            </button>
            <Link
              to="/"
              className="px-5 py-2.5 bg-gradient-to-r from-gray-600 to-gray-700 text-white rounded-xl hover:from-gray-700 hover:to-gray-800 font-semibold shadow-lg hover:shadow-xl transition-all duration-200"
            >
              ← Gallery
            </Link>
          </div>
        </div>
      </div>

      {/* Keyboard Shortcuts Help Modal */}
      {showHelp && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowHelp(false)}>
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-gray-900">Keyboard Shortcuts</h3>
              <button
                onClick={() => setShowHelp(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="font-medium text-gray-700">← or A</div>
                <div className="text-gray-600">Previous image</div>

                <div className="font-medium text-gray-700">→ or D</div>
                <div className="text-gray-600">Next image</div>

                <div className="font-medium text-gray-700">E</div>
                <div className="text-gray-600">Toggle edit mode</div>

                <div className="font-medium text-gray-700">Esc</div>
                <div className="text-gray-600">Exit edit or go back</div>

                <div className="font-medium text-gray-700">H</div>
                <div className="text-gray-600">Go to home/gallery</div>

                <div className="font-medium text-gray-700">?</div>
                <div className="text-gray-600">Show/hide this help</div>
              </div>

              {editMode && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm font-semibold text-gray-700 mb-2">Edit Mode Shortcuts:</p>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="font-medium text-gray-700">Ctrl+Z</div>
                    <div className="text-gray-600">Undo</div>

                    <div className="font-medium text-gray-700">Ctrl+Y</div>
                    <div className="text-gray-600">Redo</div>

                    <div className="font-medium text-gray-700">Delete</div>
                    <div className="text-gray-600">Delete annotation</div>

                    <div className="font-medium text-gray-700">Ctrl+D</div>
                    <div className="text-gray-600">Draw mode</div>

                    <div className="font-medium text-gray-700">Ctrl+B</div>
                    <div className="text-gray-600">Batch mode</div>

                    <div className="font-medium text-gray-700">Ctrl+A</div>
                    <div className="text-gray-600">Select all</div>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={() => setShowHelp(false)}
              className="mt-6 w-full px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 font-medium"
            >
              Got it!
            </button>
          </div>
        </div>
      )}

      {/* Image Display with Annotations */}
      <div className="bg-white rounded-2xl shadow-lg p-6 mb-8 border-t-4 border-indigo-400">
        {editMode ? (
          <AnnotationEditorV2
            imageUrl={getImageUrl(image.filename)}
            annotations={annotations}
            filename={image.filename}
            imageId={id}
            onAnnotationsChange={handleAnnotationsChange}
          />
        ) : (
          <ZoomableImage
            imageUrl={getImageUrl(image.filename)}
            annotations={annotations}
            filename={image.filename}
          />
        )}
      </div>

      {/* Annotation Details */}
      {annotations.length > 0 && (
        <div className="bg-white rounded-2xl shadow-lg p-8 border-t-4 border-green-400">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            🏷️ Annotation Details ({annotations.length})
          </h3>
          <div className="space-y-4">
            {annotations.map((ann, idx) => (
              <div
                key={ann.id || idx}
                className="border-2 border-gray-200 rounded-xl p-5 hover:border-blue-400 hover:shadow-lg transition-all duration-200 bg-gradient-to-br from-white to-gray-50"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <p className="font-bold text-gray-900 text-lg mb-2">{ann.category}</p>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center">
                        <span className="text-sm text-gray-600 font-medium">Confidence:</span>
                        <span className="ml-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-bold">
                          {(ann.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                      {ann.bbox && (
                        <p className="text-sm text-gray-600">
                          <span className="font-medium">BBox:</span> [{ann.bbox.join(', ')}]
                          {ann.area && <span className="ml-2">| <span className="font-medium">Area:</span> {ann.area.toFixed(0)} px²</span>}
                        </p>
                      )}
                    </div>
                  </div>
                  <span className={`text-sm px-4 py-2 rounded-full font-bold shadow-md ${
                    ann.status === 'pending'
                      ? 'bg-yellow-400 text-yellow-900'
                      : 'bg-green-500 text-white'
                  }`}>
                    {ann.status === 'pending' ? '🟡' : '✅'} {ann.status.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ImageViewer;
