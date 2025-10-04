import { useRef, useEffect, useState } from 'react';

/**
 * Component with zoom and pan capabilities for annotated images
 */
function ZoomableImage({ imageUrl, annotations = [], filename }) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const imgRef = useRef(null);

  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [startPan, setStartPan] = useState({ x: 0, y: 0 });
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const [showLabels, setShowLabels] = useState(true);

  // Category colors
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

  // Load image and setup
  useEffect(() => {
    const img = imgRef.current;
    if (!img) return;

    const handleImageLoad = () => {
      const { naturalWidth, naturalHeight } = img;
      setImageDimensions({ width: naturalWidth, height: naturalHeight });
      drawAnnotations();
    };

    if (img.complete) {
      handleImageLoad();
    } else {
      img.addEventListener('load', handleImageLoad);
      return () => img.removeEventListener('load', handleImageLoad);
    }
  }, [imageUrl]);

  // Redraw when zoom, pan, or annotations change
  useEffect(() => {
    drawAnnotations();
  }, [zoom, pan, annotations, showLabels, imageDimensions]);

  const drawAnnotations = () => {
    const canvas = canvasRef.current;
    const img = imgRef.current;
    const container = containerRef.current;

    if (!canvas || !img || !container) return;

    const ctx = canvas.getContext('2d');

    // Set canvas size
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Calculate scaled dimensions
    const imgWidth = imageDimensions.width * zoom;
    const imgHeight = imageDimensions.height * zoom;

    // Draw each annotation
    annotations.forEach((ann) => {
      if (!ann.bbox || ann.bbox.length !== 4) return;

      const [x, y, width, height] = ann.bbox;

      // Apply zoom and pan
      const scaledX = x * zoom + pan.x;
      const scaledY = y * zoom + pan.y;
      const scaledWidth = width * zoom;
      const scaledHeight = height * zoom;

      const color = getCategoryColor(ann.category);
      const confidence = ann.confidence || 1.0;

      // Draw bounding box
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.strokeRect(scaledX, scaledY, scaledWidth, scaledHeight);

      // Draw semi-transparent fill
      ctx.fillStyle = color + '20';
      ctx.fillRect(scaledX, scaledY, scaledWidth, scaledHeight);

      // Draw label
      if (showLabels) {
        const label = `${ann.category} ${(confidence * 100).toFixed(0)}%`;
        const fontSize = Math.max(12, 14 * zoom);
        ctx.font = `bold ${fontSize}px Arial`;

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

  // Mouse wheel zoom
  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((prevZoom) => Math.min(Math.max(0.1, prevZoom * delta), 5));
  };

  // Pan handlers
  const handleMouseDown = (e) => {
    setIsPanning(true);
    setStartPan({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e) => {
    if (!isPanning) return;
    setPan({
      x: e.clientX - startPan.x,
      y: e.clientY - startPan.y,
    });
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  // Zoom controls
  const handleZoomIn = () => {
    setZoom((prevZoom) => Math.min(prevZoom * 1.2, 5));
  };

  const handleZoomOut = () => {
    setZoom((prevZoom) => Math.max(prevZoom * 0.8, 0.1));
  };

  const handleResetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  return (
    <div className="relative">
      {/* Controls */}
      <div className="absolute top-4 right-4 z-10 bg-white rounded-lg shadow-md p-2 space-x-2">
        <button
          onClick={handleZoomIn}
          className="px-3 py-1 bg-gray-200 text-gray-700 hover:bg-gray-300 rounded text-sm font-medium"
          title="Zoom In"
        >
          +
        </button>
        <button
          onClick={handleZoomOut}
          className="px-3 py-1 bg-gray-200 text-gray-700 hover:bg-gray-300 rounded text-sm font-medium"
          title="Zoom Out"
        >
          −
        </button>
        <button
          onClick={handleResetView}
          className="px-3 py-1 bg-gray-200 text-gray-700 hover:bg-gray-300 rounded text-sm font-medium"
          title="Reset View"
        >
          ⟲
        </button>
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
        <span className="text-sm text-gray-600 px-2">
          {(zoom * 100).toFixed(0)}%
        </span>
      </div>

      {/* Image container with canvas overlay */}
      <div
        ref={containerRef}
        className="relative overflow-hidden bg-gray-100 rounded-lg"
        style={{ height: '600px', cursor: isPanning ? 'grabbing' : 'grab' }}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <img
          ref={imgRef}
          src={imageUrl}
          alt={filename}
          className="absolute"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: '0 0',
            maxWidth: 'none',
          }}
          draggable={false}
        />
        <canvas
          ref={canvasRef}
          className="absolute top-0 left-0 pointer-events-none"
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

      {/* Help text */}
      <div className="mt-2 text-xs text-gray-500 text-center">
        Use mouse wheel to zoom | Click and drag to pan
      </div>
    </div>
  );
}

export default ZoomableImage;
