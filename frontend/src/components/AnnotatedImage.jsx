import { useRef, useEffect, useState } from 'react';

/**
 * Component to display an image with bounding box annotations
 * Uses canvas overlay for drawing boxes with labels
 */
function AnnotatedImage({ imageUrl, annotations = [], filename }) {
  const canvasRef = useRef(null);
  const imgRef = useRef(null);
  const containerRef = useRef(null);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const [scale, setScale] = useState(1);
  const [showLabels, setShowLabels] = useState(true);

  // Category colors - consistent color mapping for categories
  const getCategoryColor = (category) => {
    const colors = {
      person: '#FF6B6B',
      car: '#4ECDC4',
      dog: '#FFD93D',
      cat: '#95E1D3',
      bicycle: '#6C5CE7',
      motorcycle: '#A29BFE',
      airplane: '#74B9FF',
      bus: '#FD79A8',
      train: '#FDCB6E',
      truck: '#E17055',
    };
    return colors[category?.toLowerCase()] || '#00B894';
  };

  useEffect(() => {
    const img = imgRef.current;
    if (!img) return;

    const handleImageLoad = () => {
      const { naturalWidth, naturalHeight } = img;
      const { clientWidth, clientHeight } = img;

      setImageDimensions({ width: naturalWidth, height: naturalHeight });

      // Calculate scale factor
      const scaleX = clientWidth / naturalWidth;
      const scaleY = clientHeight / naturalHeight;
      setScale(Math.min(scaleX, scaleY));

      // Draw annotations
      drawAnnotations();
    };

    if (img.complete) {
      handleImageLoad();
    } else {
      img.addEventListener('load', handleImageLoad);
      return () => img.removeEventListener('load', handleImageLoad);
    }
  }, [annotations, showLabels, imageUrl]);

  const drawAnnotations = () => {
    const canvas = canvasRef.current;
    const img = imgRef.current;

    if (!canvas || !img) return;

    const ctx = canvas.getContext('2d');

    // Set canvas size to match image display size
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Calculate scale
    const scaleX = img.clientWidth / imageDimensions.width;
    const scaleY = img.clientHeight / imageDimensions.height;

    // Draw each annotation
    annotations.forEach((ann, idx) => {
      if (!ann.bbox || ann.bbox.length !== 4) return;

      // COCO format: [x, y, width, height]
      const [x, y, width, height] = ann.bbox;

      // Scale to display size
      const scaledX = x * scaleX;
      const scaledY = y * scaleY;
      const scaledWidth = width * scaleX;
      const scaledHeight = height * scaleY;

      const color = getCategoryColor(ann.category);
      const confidence = ann.confidence || 1.0;

      // Draw bounding box
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.strokeRect(scaledX, scaledY, scaledWidth, scaledHeight);

      // Draw semi-transparent fill
      ctx.fillStyle = color + '20'; // 20% opacity
      ctx.fillRect(scaledX, scaledY, scaledWidth, scaledHeight);

      // Draw label if enabled
      if (showLabels) {
        const label = `${ann.category} ${(confidence * 100).toFixed(0)}%`;
        const fontSize = 14;
        ctx.font = `bold ${fontSize}px Arial`;

        // Measure text
        const textMetrics = ctx.measureText(label);
        const textWidth = textMetrics.width;
        const textHeight = fontSize;
        const padding = 4;

        // Draw label background
        ctx.fillStyle = color;
        ctx.fillRect(
          scaledX,
          scaledY - textHeight - padding * 2,
          textWidth + padding * 2,
          textHeight + padding * 2
        );

        // Draw label text
        ctx.fillStyle = 'white';
        ctx.fillText(label, scaledX + padding, scaledY - padding);
      }
    });
  };

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (imgRef.current) {
        drawAnnotations();
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [annotations, showLabels]);

  return (
    <div className="relative" ref={containerRef}>
      {/* Controls */}
      <div className="absolute top-4 right-4 z-10 bg-white rounded-lg shadow-md p-2 space-x-2">
        <button
          onClick={() => setShowLabels(!showLabels)}
          className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
            showLabels
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          {showLabels ? 'Hide Labels' : 'Show Labels'}
        </button>
      </div>

      {/* Image with canvas overlay */}
      <div className="relative inline-block">
        <img
          ref={imgRef}
          src={imageUrl}
          alt={filename}
          className="max-w-full h-auto"
          crossOrigin="anonymous"
        />
        <canvas
          ref={canvasRef}
          className="absolute top-0 left-0 pointer-events-none"
          style={{ width: '100%', height: '100%' }}
        />
      </div>

      {/* Annotation legend */}
      {annotations.length > 0 && (
        <div className="mt-4 bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
            Annotations ({annotations.length})
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {annotations.map((ann, idx) => (
              <div key={idx} className="flex items-center space-x-2">
                <div
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: getCategoryColor(ann.category) }}
                />
                <span className="text-sm text-gray-700">
                  {ann.category} ({(ann.confidence * 100).toFixed(0)}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default AnnotatedImage;
