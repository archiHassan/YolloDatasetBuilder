import { useRef, useEffect, useState } from 'react';
import { createAnnotation, updateAnnotation, deleteAnnotation } from '../api/client';

/**
 * Interactive annotation editor with drawing, moving, resizing, and deleting
 */
function AnnotationEditor({ imageUrl, annotations = [], filename, imageId, onAnnotationsChange }) {
  const canvasRef = useRef(null);
  const imgRef = useRef(null);
  const containerRef = useRef(null);

  const [localAnnotations, setLocalAnnotations] = useState(annotations);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const [mode, setMode] = useState('view'); // 'view', 'draw', 'edit'
  const [selectedAnnotation, setSelectedAnnotation] = useState(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [resizeHandle, setResizeHandle] = useState(null);
  const [drawStart, setDrawStart] = useState(null);
  const [currentBox, setCurrentBox] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('person');
  const [hasChanges, setHasChanges] = useState(false);

  // Available categories
  const categories = [
    'person', 'car', 'dog', 'cat', 'bicycle', 'motorcycle',
    'airplane', 'bus', 'train', 'truck', 'pizza', 'sandwich'
  ];

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
      pizza: '#FFA502',
      sandwich: '#FF7979',
    };
    return colors[category?.toLowerCase()] || '#00B894';
  };

  // Sync with prop changes
  useEffect(() => {
    setLocalAnnotations(annotations);
  }, [annotations]);

  // Load image
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

  // Redraw when annotations or selection changes
  useEffect(() => {
    drawAnnotations();
  }, [localAnnotations, selectedAnnotation, currentBox]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Delete' && selectedAnnotation !== null) {
        handleDeleteAnnotation(selectedAnnotation);
      }
      if (e.key === 'Escape') {
        setSelectedAnnotation(null);
        setMode('view');
        setIsDrawing(false);
        setCurrentBox(null);
      }
      if (e.key === 'd' && e.ctrlKey) {
        e.preventDefault();
        setMode('draw');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedAnnotation]);

  const drawAnnotations = () => {
    const canvas = canvasRef.current;
    const img = imgRef.current;

    if (!canvas || !img) return;

    const ctx = canvas.getContext('2d');
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const scaleX = img.clientWidth / imageDimensions.width;
    const scaleY = img.clientHeight / imageDimensions.height;

    // Draw all annotations
    localAnnotations.forEach((ann, idx) => {
      if (!ann.bbox || ann.bbox.length !== 4) return;

      const [x, y, width, height] = ann.bbox;
      const scaledX = x * scaleX;
      const scaledY = y * scaleY;
      const scaledWidth = width * scaleX;
      const scaledHeight = height * scaleY;

      const color = getCategoryColor(ann.category);
      const isSelected = selectedAnnotation === idx;

      // Draw box
      ctx.strokeStyle = isSelected ? '#000' : color;
      ctx.lineWidth = isSelected ? 3 : 2;
      ctx.strokeRect(scaledX, scaledY, scaledWidth, scaledHeight);

      // Fill
      ctx.fillStyle = color + '20';
      ctx.fillRect(scaledX, scaledY, scaledWidth, scaledHeight);

      // Draw resize handles if selected
      if (isSelected) {
        const handleSize = 8;
        ctx.fillStyle = '#000';

        // Corner handles
        ctx.fillRect(scaledX - handleSize/2, scaledY - handleSize/2, handleSize, handleSize);
        ctx.fillRect(scaledX + scaledWidth - handleSize/2, scaledY - handleSize/2, handleSize, handleSize);
        ctx.fillRect(scaledX - handleSize/2, scaledY + scaledHeight - handleSize/2, handleSize, handleSize);
        ctx.fillRect(scaledX + scaledWidth - handleSize/2, scaledY + scaledHeight - handleSize/2, handleSize, handleSize);
      }

      // Draw label
      const label = `${ann.category} ${((ann.confidence || 1) * 100).toFixed(0)}%`;
      ctx.font = 'bold 14px Arial';
      const textMetrics = ctx.measureText(label);
      const padding = 4;

      ctx.fillStyle = color;
      ctx.fillRect(scaledX, scaledY - 22, textMetrics.width + padding * 2, 22);
      ctx.fillStyle = 'white';
      ctx.fillText(label, scaledX + padding, scaledY - 6);
    });

    // Draw current box being drawn
    if (currentBox) {
      const { x, y, width, height } = currentBox;
      ctx.strokeStyle = getCategoryColor(selectedCategory);
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.strokeRect(x, y, width, height);
      ctx.setLineDash([]);
    }
  };

  const getMousePos = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  };

  const getResizeHandle = (mouseX, mouseY, box, scaleX, scaleY) => {
    const [x, y, width, height] = box;
    const scaledX = x * scaleX;
    const scaledY = y * scaleY;
    const scaledWidth = width * scaleX;
    const scaledHeight = height * scaleY;
    const handleSize = 8;

    const handles = [
      { name: 'nw', x: scaledX, y: scaledY },
      { name: 'ne', x: scaledX + scaledWidth, y: scaledY },
      { name: 'sw', x: scaledX, y: scaledY + scaledHeight },
      { name: 'se', x: scaledX + scaledWidth, y: scaledY + scaledHeight },
    ];

    for (const handle of handles) {
      if (
        mouseX >= handle.x - handleSize &&
        mouseX <= handle.x + handleSize &&
        mouseY >= handle.y - handleSize &&
        mouseY <= handle.y + handleSize
      ) {
        return handle.name;
      }
    }
    return null;
  };

  const isPointInBox = (mouseX, mouseY, box, scaleX, scaleY) => {
    const [x, y, width, height] = box;
    const scaledX = x * scaleX;
    const scaledY = y * scaleY;
    const scaledWidth = width * scaleX;
    const scaledHeight = height * scaleY;

    return (
      mouseX >= scaledX &&
      mouseX <= scaledX + scaledWidth &&
      mouseY >= scaledY &&
      mouseY <= scaledY + scaledHeight
    );
  };

  const handleMouseDown = (e) => {
    const pos = getMousePos(e);
    const img = imgRef.current;
    const scaleX = img.clientWidth / imageDimensions.width;
    const scaleY = img.clientHeight / imageDimensions.height;

    if (mode === 'draw') {
      setIsDrawing(true);
      setDrawStart(pos);
      setCurrentBox({ x: pos.x, y: pos.y, width: 0, height: 0 });
      return;
    }

    // Check if clicking on selected annotation's resize handle
    if (selectedAnnotation !== null) {
      const ann = localAnnotations[selectedAnnotation];
      const handle = getResizeHandle(pos.x, pos.y, ann.bbox, scaleX, scaleY);
      if (handle) {
        setIsResizing(true);
        setResizeHandle(handle);
        setDrawStart(pos);
        return;
      }
    }

    // Check if clicking on any annotation
    for (let i = localAnnotations.length - 1; i >= 0; i--) {
      const ann = localAnnotations[i];
      if (isPointInBox(pos.x, pos.y, ann.bbox, scaleX, scaleY)) {
        setSelectedAnnotation(i);
        setIsDragging(true);
        setDrawStart(pos);
        return;
      }
    }

    // Clicked on empty space
    setSelectedAnnotation(null);
  };

  const handleMouseMove = (e) => {
    const pos = getMousePos(e);

    if (isDrawing && drawStart) {
      const width = pos.x - drawStart.x;
      const height = pos.y - drawStart.y;
      setCurrentBox({
        x: width < 0 ? pos.x : drawStart.x,
        y: height < 0 ? pos.y : drawStart.y,
        width: Math.abs(width),
        height: Math.abs(height),
      });
    }

    if (isDragging && selectedAnnotation !== null && drawStart) {
      const dx = pos.x - drawStart.x;
      const dy = pos.y - drawStart.y;
      const img = imgRef.current;
      const scaleX = imageDimensions.width / img.clientWidth;
      const scaleY = imageDimensions.height / img.clientHeight;

      const newAnnotations = [...localAnnotations];
      const ann = { ...newAnnotations[selectedAnnotation] };
      ann.bbox = [
        ann.bbox[0] + dx * scaleX,
        ann.bbox[1] + dy * scaleY,
        ann.bbox[2],
        ann.bbox[3],
      ];
      newAnnotations[selectedAnnotation] = ann;
      setLocalAnnotations(newAnnotations);
      setDrawStart(pos);
      setHasChanges(true);
    }

    if (isResizing && selectedAnnotation !== null && drawStart) {
      const dx = pos.x - drawStart.x;
      const dy = pos.y - drawStart.y;
      const img = imgRef.current;
      const scaleX = imageDimensions.width / img.clientWidth;
      const scaleY = imageDimensions.height / img.clientHeight;

      const newAnnotations = [...localAnnotations];
      const ann = { ...newAnnotations[selectedAnnotation] };
      const [x, y, width, height] = ann.bbox;

      if (resizeHandle === 'se') {
        ann.bbox = [x, y, width + dx * scaleX, height + dy * scaleY];
      } else if (resizeHandle === 'sw') {
        ann.bbox = [x + dx * scaleX, y, width - dx * scaleX, height + dy * scaleY];
      } else if (resizeHandle === 'ne') {
        ann.bbox = [x, y + dy * scaleY, width + dx * scaleX, height - dy * scaleY];
      } else if (resizeHandle === 'nw') {
        ann.bbox = [x + dx * scaleX, y + dy * scaleY, width - dx * scaleX, height - dy * scaleY];
      }

      newAnnotations[selectedAnnotation] = ann;
      setLocalAnnotations(newAnnotations);
      setDrawStart(pos);
      setHasChanges(true);
    }
  };

  const handleMouseUp = () => {
    if (isDrawing && currentBox && currentBox.width > 10 && currentBox.height > 10) {
      const img = imgRef.current;
      const scaleX = imageDimensions.width / img.clientWidth;
      const scaleY = imageDimensions.height / img.clientHeight;

      const newAnnotation = {
        id: Date.now(),
        bbox: [
          currentBox.x * scaleX,
          currentBox.y * scaleY,
          currentBox.width * scaleX,
          currentBox.height * scaleY,
        ],
        category: selectedCategory,
        confidence: 1.0,
        status: 'pending',
      };

      setLocalAnnotations([...localAnnotations, newAnnotation]);
      setHasChanges(true);
      setMode('view');
    }

    setIsDrawing(false);
    setIsDragging(false);
    setIsResizing(false);
    setResizeHandle(null);
    setDrawStart(null);
    setCurrentBox(null);
  };

  const handleDeleteAnnotation = (index) => {
    const newAnnotations = localAnnotations.filter((_, i) => i !== index);
    setLocalAnnotations(newAnnotations);
    setSelectedAnnotation(null);
    setHasChanges(true);
  };

  const handleSaveChanges = async () => {
    try {
      // Save all annotations to backend
      // For MVP, we'll just notify parent component
      if (onAnnotationsChange) {
        onAnnotationsChange(localAnnotations);
      }
      setHasChanges(false);
      alert('Changes saved successfully!');
    } catch (err) {
      console.error('Error saving annotations:', err);
      alert('Failed to save changes: ' + err.message);
    }
  };

  const handleDiscardChanges = () => {
    setLocalAnnotations(annotations);
    setHasChanges(false);
    setSelectedAnnotation(null);
  };

  return (
    <div className="relative">
      {/* Toolbar */}
      <div className="mb-4 bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          {/* Mode buttons */}
          <div className="flex space-x-2">
            <button
              onClick={() => setMode('view')}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                mode === 'view'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              👁 View
            </button>
            <button
              onClick={() => setMode('draw')}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                mode === 'draw'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              ✏ Draw
            </button>
          </div>

          {/* Category selector */}
          {mode === 'draw' && (
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Category:</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
              <div
                className="w-6 h-6 rounded border-2 border-gray-300"
                style={{ backgroundColor: getCategoryColor(selectedCategory) }}
              />
            </div>
          )}

          {/* Action buttons */}
          <div className="flex space-x-2">
            {selectedAnnotation !== null && (
              <button
                onClick={() => handleDeleteAnnotation(selectedAnnotation)}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 font-medium"
              >
                🗑 Delete
              </button>
            )}
            {hasChanges && (
              <>
                <button
                  onClick={handleSaveChanges}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 font-medium"
                >
                  💾 Save
                </button>
                <button
                  onClick={handleDiscardChanges}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 font-medium"
                >
                  ↩ Discard
                </button>
              </>
            )}
          </div>
        </div>

        {/* Help text */}
        <div className="mt-2 text-xs text-gray-600">
          {mode === 'view' && 'Click on a box to select it. Press Delete to remove.'}
          {mode === 'draw' && 'Click and drag to draw a new bounding box.'}
          {' | Keyboard: Ctrl+D (draw mode), Delete (remove), Esc (cancel)'}
        </div>
      </div>

      {/* Canvas container */}
      <div ref={containerRef} className="relative bg-gray-100 rounded-lg overflow-hidden">
        <img
          ref={imgRef}
          src={imageUrl}
          alt={filename}
          className="max-w-full h-auto"
          draggable={false}
        />
        <canvas
          ref={canvasRef}
          className="absolute top-0 left-0 cursor-crosshair"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        />
      </div>

      {/* Annotation list */}
      <div className="mt-4 bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">
          Annotations ({localAnnotations.length})
        </h4>
        <div className="space-y-2 max-h-40 overflow-y-auto">
          {localAnnotations.map((ann, idx) => (
            <div
              key={idx}
              onClick={() => setSelectedAnnotation(idx)}
              className={`flex items-center justify-between p-2 rounded cursor-pointer transition-colors ${
                selectedAnnotation === idx
                  ? 'bg-blue-100 border-2 border-blue-500'
                  : 'bg-white hover:bg-gray-100'
              }`}
            >
              <div className="flex items-center space-x-2">
                <div
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: getCategoryColor(ann.category) }}
                />
                <span className="text-sm font-medium text-gray-700">
                  {ann.category} ({((ann.confidence || 1) * 100).toFixed(0)}%)
                </span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteAnnotation(idx);
                }}
                className="text-red-600 hover:text-red-800 text-xs"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default AnnotationEditor;
