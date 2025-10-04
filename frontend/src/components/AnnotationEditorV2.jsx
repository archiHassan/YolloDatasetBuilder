import { useRef, useEffect, useState } from 'react';
import { useAnnotationHistory } from '../hooks/useAnnotationHistory';
import TemplateManager from './TemplateManager';
import { incrementTemplateUsage, generateMockSAMMask, getSAMStatus } from '../api/client';

/**
 * Enhanced annotation editor with undo/redo, batch operations, and confidence adjustment
 */
function AnnotationEditorV2({ imageUrl, annotations = [], filename, imageId, onAnnotationsChange }) {
  const canvasRef = useRef(null);
  const imgRef = useRef(null);
  const containerRef = useRef(null);

  // Use history hook for undo/redo
  const {
    annotations: localAnnotations,
    updateAnnotations,
    undo,
    redo,
    canUndo,
    canRedo,
    resetHistory,
  } = useAnnotationHistory(annotations);

  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const [mode, setMode] = useState('view');
  const [annotationType, setAnnotationType] = useState('bbox'); // 'bbox' or 'polygon'
  const [selectedAnnotation, setSelectedAnnotation] = useState(null);
  const [selectedAnnotations, setSelectedAnnotations] = useState([]); // For batch operations
  const [isDrawing, setIsDrawing] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [resizeHandle, setResizeHandle] = useState(null);
  const [drawStart, setDrawStart] = useState(null);
  const [currentBox, setCurrentBox] = useState(null);

  // Polygon-specific state
  const [polygonPoints, setPolygonPoints] = useState([]);
  const [isDrawingPolygon, setIsDrawingPolygon] = useState(false);
  const [hoveredPoint, setHoveredPoint] = useState(null);

  const [selectedCategory, setSelectedCategory] = useState('person');
  const [confidenceValue, setConfidenceValue] = useState(1.0);
  const [hasChanges, setHasChanges] = useState(false);
  const [batchMode, setBatchMode] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [showAnnotations, setShowAnnotations] = useState(true);
  const [showTemplateManager, setShowTemplateManager] = useState(false);
  const [samMode, setSamMode] = useState(false);
  const [samPoints, setSamPoints] = useState([]);
  const [samLoading, setSamLoading] = useState(false);

  const categories = [
    'person', 'car', 'dog', 'cat', 'bicycle', 'motorcycle',
    'airplane', 'bus', 'train', 'truck', 'pizza', 'sandwich'
  ];

  const getCategoryColor = (category) => {
    const colors = {
      person: '#FF6B6B', car: '#4ECDC4', dog: '#FFD93D', cat: '#95E1D3',
      bicycle: '#6C5CE7', motorcycle: '#A29BFE', airplane: '#74B9FF', bus: '#FD79A8',
      train: '#FDCB6E', truck: '#E17055', pizza: '#FFA502', sandwich: '#FF7979',
    };
    return colors[category?.toLowerCase()] || '#00B894';
  };

  // Sync with prop changes
  useEffect(() => {
    resetHistory(annotations);
  }, [annotations, resetHistory]);

  useEffect(() => {
    const img = imgRef.current;
    if (!img) return;

    const handleImageLoad = () => {
      const { naturalWidth, naturalHeight } = img;
      setImageDimensions({ width: naturalWidth, height: naturalHeight });
      // Force canvas resize and redraw after image loads
      setTimeout(() => drawAnnotations(), 100);
    };

    if (img.complete && img.naturalWidth > 0) {
      handleImageLoad();
    } else {
      img.addEventListener('load', handleImageLoad);
      return () => img.removeEventListener('load', handleImageLoad);
    }
  }, [imageUrl]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      drawAnnotations();
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [localAnnotations, selectedAnnotation, selectedAnnotations, currentBox]);

  useEffect(() => {
    drawAnnotations();
  }, [localAnnotations, selectedAnnotation, selectedAnnotations, currentBox]);

  // Enhanced Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't trigger shortcuts when typing in input fields
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
        return;
      }

      // Undo/Redo
      if (e.ctrlKey && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (undo()) {
          setHasChanges(true);
        }
      }
      if (e.ctrlKey && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        if (redo()) {
          setHasChanges(true);
        }
      }

      // Delete (Delete key or Backspace)
      if (e.key === 'Delete' || e.key === 'Backspace') {
        e.preventDefault();
        if (batchMode && selectedAnnotations.length > 0) {
          handleBatchDelete();
        } else if (selectedAnnotation !== null) {
          handleDeleteAnnotation(selectedAnnotation);
        }
      }

      // Escape - Cancel/Exit
      if (e.key === 'Escape') {
        if (isDrawingPolygon) {
          setPolygonPoints([]);
          setIsDrawingPolygon(false);
        }
        setSelectedAnnotation(null);
        setSelectedAnnotations([]);
        setMode('view');
        setIsDrawing(false);
        setCurrentBox(null);
        setBatchMode(false);
      }

      // Mode switching
      if (e.key === 'd' && e.ctrlKey) {
        e.preventDefault();
        setMode('draw');
        setBatchMode(false);
      }
      if (e.key === 'b' && e.ctrlKey) {
        e.preventDefault();
        setBatchMode(!batchMode);
        setMode('view');
      }
      if (e.key === 'v' && !e.ctrlKey) {
        // V for View mode
        e.preventDefault();
        setMode('view');
        setBatchMode(false);
      }

      // Annotation type toggle (R for Rectangle, P for Polygon)
      if (e.key === 'r' && !e.ctrlKey && mode === 'draw') {
        e.preventDefault();
        setAnnotationType('bbox');
        setPolygonPoints([]);
        setIsDrawingPolygon(false);
      }
      if (e.key === 'p' && !e.ctrlKey && mode === 'draw') {
        e.preventDefault();
        setAnnotationType('polygon');
        setCurrentBox(null);
        setIsDrawing(false);
      }

      // Quick category selection (Number keys 1-9)
      const numKey = parseInt(e.key);
      if (!isNaN(numKey) && numKey >= 1 && numKey <= 9 && !e.ctrlKey) {
        const categoryIndex = numKey - 1;
        if (categoryIndex < categories.length) {
          e.preventDefault();
          setSelectedCategory(categories[categoryIndex]);
        }
      }

      // Tab - Cycle through annotations
      if (e.key === 'Tab') {
        e.preventDefault();
        if (localAnnotations.length > 0) {
          const currentIdx = selectedAnnotation !== null ? selectedAnnotation : -1;
          const nextIdx = (currentIdx + 1) % localAnnotations.length;
          setSelectedAnnotation(nextIdx);
        }
      }

      // Select all (Ctrl+A in batch mode)
      if (e.key === 'a' && e.ctrlKey && batchMode) {
        e.preventDefault();
        setSelectedAnnotations(localAnnotations.map((_, i) => i));
      }

      // Save (Ctrl+S)
      if (e.key === 's' && e.ctrlKey) {
        e.preventDefault();
        if (hasChanges) {
          handleSaveChanges();
        }
      }

      // Confidence adjustment (+ and -)
      if ((e.key === '+' || e.key === '=') && selectedAnnotation !== null) {
        e.preventDefault();
        const newConf = Math.min(1.0, (localAnnotations[selectedAnnotation].confidence || 1.0) + 0.1);
        handleConfidenceChange(newConf);
      }
      if ((e.key === '-' || e.key === '_') && selectedAnnotation !== null) {
        e.preventDefault();
        const newConf = Math.max(0.1, (localAnnotations[selectedAnnotation].confidence || 1.0) - 0.1);
        handleConfidenceChange(newConf);
      }

      // Duplicate annotation (Ctrl+D when annotation selected)
      if (e.key === 'd' && e.ctrlKey && selectedAnnotation !== null && !mode) {
        e.preventDefault();
        const ann = localAnnotations[selectedAnnotation];
        const duplicated = {
          ...ann,
          id: Date.now(),
        };

        // Offset the duplicate slightly
        if (duplicated.bbox) {
          duplicated.bbox = [
            duplicated.bbox[0] + 10,
            duplicated.bbox[1] + 10,
            duplicated.bbox[2],
            duplicated.bbox[3]
          ];
        } else if (duplicated.points) {
          duplicated.points = duplicated.points.map(([x, y]) => [x + 10, y + 10]);
        }

        updateAnnotations([...localAnnotations, duplicated]);
        setHasChanges(true);
        setSelectedAnnotation(localAnnotations.length);
      }

      // C - Copy selected annotation
      if (e.key === 'c' && !e.ctrlKey && selectedAnnotation !== null) {
        e.preventDefault();
        const ann = localAnnotations[selectedAnnotation];
        const copyData = {
          annotation: ann,
          sourceImageId: imageId,
          timestamp: Date.now()
        };
        localStorage.setItem('copiedAnnotation', JSON.stringify(copyData));
        console.log('Annotation copied to clipboard');
      }

      // X - Cut selected annotation (copy + delete)
      if (e.key === 'x' && !e.ctrlKey && selectedAnnotation !== null) {
        e.preventDefault();
        const ann = localAnnotations[selectedAnnotation];
        const copyData = {
          annotation: ann,
          sourceImageId: imageId,
          timestamp: Date.now()
        };
        localStorage.setItem('copiedAnnotation', JSON.stringify(copyData));

        // Delete the annotation inline
        const newAnnotations = localAnnotations.filter((_, i) => i !== selectedAnnotation);
        updateAnnotations(newAnnotations);
        setSelectedAnnotation(null);
        setHasChanges(true);

        console.log('Annotation cut to clipboard');
      }

      // V - Paste annotation (Ctrl+V)
      if (e.key === 'v' && e.ctrlKey && !batchMode && mode !== 'draw') {
        e.preventDefault();
        const copiedData = localStorage.getItem('copiedAnnotation');
        if (copiedData) {
          try {
            const { annotation: ann, sourceImageId } = JSON.parse(copiedData);
            const pasted = {
              ...ann,
              id: Date.now(),
              status: 'pending'
            };

            // Offset the pasted annotation
            if (pasted.bbox) {
              pasted.bbox = [
                pasted.bbox[0] + 20,
                pasted.bbox[1] + 20,
                pasted.bbox[2],
                pasted.bbox[3]
              ];
            } else if (pasted.points) {
              pasted.points = pasted.points.map(([x, y]) => [x + 20, y + 20]);
            }

            updateAnnotations([...localAnnotations, pasted]);
            setHasChanges(true);
            setSelectedAnnotation(localAnnotations.length);

            const crossImage = sourceImageId !== imageId;
            console.log(`Annotation pasted${crossImage ? ' from another image' : ''}`);
          } catch (err) {
            console.error('Failed to paste annotation:', err);
          }
        }
      }

      // Space - Toggle annotation visibility
      if (e.key === ' ') {
        e.preventDefault();
        setShowAnnotations(!showAnnotations);
      }

      // Arrow keys for fine-tuning selected annotation position
      if (selectedAnnotation !== null && !batchMode && !e.ctrlKey) {
        const moveStep = e.shiftKey ? 10 : 1; // Shift+Arrow = 10px, Arrow = 1px
        const newAnnotations = [...localAnnotations];
        const ann = { ...newAnnotations[selectedAnnotation] };
        let moved = false;

        if (ann.bbox && (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
          e.preventDefault();
          const [x, y, w, h] = ann.bbox;

          switch (e.key) {
            case 'ArrowUp':
              ann.bbox = [x, y - moveStep, w, h];
              moved = true;
              break;
            case 'ArrowDown':
              ann.bbox = [x, y + moveStep, w, h];
              moved = true;
              break;
            case 'ArrowLeft':
              ann.bbox = [x - moveStep, y, w, h];
              moved = true;
              break;
            case 'ArrowRight':
              ann.bbox = [x + moveStep, y, w, h];
              moved = true;
              break;
          }
        } else if (ann.points && (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
          e.preventDefault();

          switch (e.key) {
            case 'ArrowUp':
              ann.points = ann.points.map(([x, y]) => [x, y - moveStep]);
              moved = true;
              break;
            case 'ArrowDown':
              ann.points = ann.points.map(([x, y]) => [x, y + moveStep]);
              moved = true;
              break;
            case 'ArrowLeft':
              ann.points = ann.points.map(([x, y]) => [x - moveStep, y]);
              moved = true;
              break;
            case 'ArrowRight':
              ann.points = ann.points.map(([x, y]) => [x + moveStep, y]);
              moved = true;
              break;
          }
        }

        if (moved) {
          newAnnotations[selectedAnnotation] = ann;
          updateAnnotations(newAnnotations);
          setHasChanges(true);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedAnnotation, selectedAnnotations, batchMode, undo, redo, localAnnotations, mode, imageId, updateAnnotations, showAnnotations, setHasChanges, setSelectedAnnotation]);

  const drawAnnotations = () => {
    const canvas = canvasRef.current;
    const img = imgRef.current;

    if (!canvas || !img || !img.clientWidth || !img.clientHeight) return;

    const ctx = canvas.getContext('2d');

    // Set canvas dimensions to match displayed image
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // If image dimensions not loaded yet, skip
    if (!imageDimensions.width || !imageDimensions.height) return;

    // If annotations are hidden, skip drawing
    if (!showAnnotations) return;

    const scaleX = img.clientWidth / imageDimensions.width;
    const scaleY = img.clientHeight / imageDimensions.height;

    localAnnotations.forEach((ann, idx) => {
      const color = getCategoryColor(ann.category);
      const isSelected = selectedAnnotation === idx || selectedAnnotations.includes(idx);

      // Draw polygon annotations
      if (ann.type === 'polygon' && ann.points && ann.points.length >= 3) {
        const scaledPoints = ann.points.map(([x, y]) => [x * scaleX, y * scaleY]);

        // Draw polygon
        ctx.beginPath();
        ctx.moveTo(scaledPoints[0][0], scaledPoints[0][1]);
        for (let i = 1; i < scaledPoints.length; i++) {
          ctx.lineTo(scaledPoints[i][0], scaledPoints[i][1]);
        }
        ctx.closePath();

        // Fill polygon
        ctx.fillStyle = color + (isSelected ? '40' : '20');
        ctx.fill();

        // Stroke polygon
        ctx.strokeStyle = isSelected ? '#000' : color;
        ctx.lineWidth = isSelected ? 3 : 2;
        ctx.stroke();

        // Draw control points if selected
        if (isSelected && selectedAnnotation === idx && !batchMode) {
          scaledPoints.forEach(([px, py]) => {
            ctx.fillStyle = '#000';
            ctx.beginPath();
            ctx.arc(px, py, 5, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#FFF';
            ctx.lineWidth = 2;
            ctx.stroke();
          });
        }

        // Get label position (use first point)
        const labelX = scaledPoints[0][0];
        const labelY = scaledPoints[0][1];
        const label = `${ann.category} ${((ann.confidence || 1) * 100).toFixed(0)}%`;
        ctx.font = 'bold 14px Arial';
        const textMetrics = ctx.measureText(label);
        const padding = 4;

        ctx.fillStyle = color;
        ctx.fillRect(labelX, labelY - 22, textMetrics.width + padding * 2, 22);
        ctx.fillStyle = 'white';
        ctx.fillText(label, labelX + padding, labelY - 6);

        return;
      }

      // Draw bounding box annotations
      if (!ann.bbox || ann.bbox.length !== 4) return;

      const [x, y, width, height] = ann.bbox;
      const scaledX = x * scaleX;
      const scaledY = y * scaleY;
      const scaledWidth = width * scaleX;
      const scaledHeight = height * scaleY;

      // Draw box
      ctx.strokeStyle = isSelected ? '#000' : color;
      ctx.lineWidth = isSelected ? 3 : 2;
      ctx.strokeRect(scaledX, scaledY, scaledWidth, scaledHeight);

      // Fill
      ctx.fillStyle = color + (isSelected ? '40' : '20');
      ctx.fillRect(scaledX, scaledY, scaledWidth, scaledHeight);

      // Draw resize handles if single selection
      if (isSelected && selectedAnnotation === idx && !batchMode) {
        const handleSize = 8;
        ctx.fillStyle = '#000';
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

      // Draw batch selection checkbox
      if (batchMode) {
        const checkSize = 20;
        ctx.fillStyle = isSelected ? '#4CAF50' : 'white';
        ctx.fillRect(scaledX + scaledWidth - checkSize - 5, scaledY + 5, checkSize, checkSize);
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 2;
        ctx.strokeRect(scaledX + scaledWidth - checkSize - 5, scaledY + 5, checkSize, checkSize);
        if (isSelected) {
          ctx.strokeStyle = 'white';
          ctx.lineWidth = 3;
          ctx.beginPath();
          ctx.moveTo(scaledX + scaledWidth - checkSize, scaledY + 12);
          ctx.lineTo(scaledX + scaledWidth - 12, scaledY + 18);
          ctx.lineTo(scaledX + scaledWidth - 8, scaledY + 10);
          ctx.stroke();
        }
      }
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

    // Draw current polygon being drawn
    if (isDrawingPolygon && polygonPoints.length > 0) {
      const color = getCategoryColor(selectedCategory);

      // Draw lines between points
      ctx.beginPath();
      ctx.moveTo(polygonPoints[0].x, polygonPoints[0].y);
      for (let i = 1; i < polygonPoints.length; i++) {
        ctx.lineTo(polygonPoints[i].x, polygonPoints[i].y);
      }
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Draw points
      polygonPoints.forEach((point, idx) => {
        ctx.fillStyle = idx === 0 ? '#00FF00' : color;
        ctx.beginPath();
        ctx.arc(point.x, point.y, 6, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#FFF';
        ctx.lineWidth = 2;
        ctx.stroke();
      });

      // Draw line to close polygon if near first point
      if (polygonPoints.length >= 3 && hoveredPoint === 0) {
        const lastPoint = polygonPoints[polygonPoints.length - 1];
        ctx.beginPath();
        ctx.moveTo(lastPoint.x, lastPoint.y);
        ctx.lineTo(polygonPoints[0].x, polygonPoints[0].y);
        ctx.strokeStyle = '#00FF00';
        ctx.lineWidth = 3;
        ctx.stroke();
      }
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
    // SAM mode takes priority
    if (samMode) {
      handleSAMClick(e);
      return;
    }

    const pos = getMousePos(e);
    const img = imgRef.current;
    const scaleX = img.clientWidth / imageDimensions.width;
    const scaleY = img.clientHeight / imageDimensions.height;

    // Polygon drawing mode
    if (mode === 'draw' && annotationType === 'polygon') {
      // Check if clicking near first point to close polygon
      if (isDrawingPolygon && polygonPoints.length >= 3) {
        const firstPoint = polygonPoints[0];
        const distance = Math.sqrt(
          Math.pow(pos.x - firstPoint.x, 2) + Math.pow(pos.y - firstPoint.y, 2)
        );

        if (distance < 10) {
          // Close polygon and save
          const img = imgRef.current;
          const scaleX = imageDimensions.width / img.clientWidth;
          const scaleY = imageDimensions.height / img.clientHeight;

          const normalizedPoints = polygonPoints.map(p => [
            p.x * scaleX,
            p.y * scaleY
          ]);

          const newAnnotation = {
            id: Date.now(),
            type: 'polygon',
            points: normalizedPoints,
            category: selectedCategory,
            confidence: confidenceValue,
            status: 'pending',
          };

          updateAnnotations([...localAnnotations, newAnnotation]);
          setHasChanges(true);
          setPolygonPoints([]);
          setIsDrawingPolygon(false);
          setMode('view');
          return;
        }
      }

      // Add new point to polygon
      setPolygonPoints([...polygonPoints, pos]);
      setIsDrawingPolygon(true);
      return;
    }

    // Rectangle drawing mode
    if (mode === 'draw' && annotationType === 'bbox') {
      setIsDrawing(true);
      setDrawStart(pos);
      setCurrentBox({ x: pos.x, y: pos.y, width: 0, height: 0 });
      return;
    }

    // Batch selection mode
    if (batchMode) {
      for (let i = localAnnotations.length - 1; i >= 0; i--) {
        const ann = localAnnotations[i];
        if (isPointInBox(pos.x, pos.y, ann.bbox, scaleX, scaleY)) {
          if (selectedAnnotations.includes(i)) {
            setSelectedAnnotations(selectedAnnotations.filter(idx => idx !== i));
          } else {
            setSelectedAnnotations([...selectedAnnotations, i]);
          }
          return;
        }
      }
      return;
    }

    // Check resize handle
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

    // Check annotation selection
    for (let i = localAnnotations.length - 1; i >= 0; i--) {
      const ann = localAnnotations[i];
      if (isPointInBox(pos.x, pos.y, ann.bbox, scaleX, scaleY)) {
        setSelectedAnnotation(i);
        setIsDragging(true);
        setDrawStart(pos);
        return;
      }
    }

    setSelectedAnnotation(null);
  };

  const handleMouseMove = (e) => {
    const pos = getMousePos(e);

    // Check if hovering over first point in polygon mode
    if (isDrawingPolygon && polygonPoints.length >= 3) {
      const firstPoint = polygonPoints[0];
      const distance = Math.sqrt(
        Math.pow(pos.x - firstPoint.x, 2) + Math.pow(pos.y - firstPoint.y, 2)
      );

      if (distance < 10) {
        setHoveredPoint(0);
      } else {
        setHoveredPoint(null);
      }
    }

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
      updateAnnotations(newAnnotations);
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
      updateAnnotations(newAnnotations);
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
        confidence: confidenceValue,
        status: 'pending',
      };

      updateAnnotations([...localAnnotations, newAnnotation]);
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
    updateAnnotations(newAnnotations);
    setSelectedAnnotation(null);
    setHasChanges(true);
  };

  const handleBatchDelete = () => {
    const newAnnotations = localAnnotations.filter((_, i) => !selectedAnnotations.includes(i));
    updateAnnotations(newAnnotations);
    setSelectedAnnotations([]);
    setHasChanges(true);
  };

  const handleBatchChangeCategory = (newCategory) => {
    const newAnnotations = [...localAnnotations];
    selectedAnnotations.forEach(idx => {
      newAnnotations[idx] = { ...newAnnotations[idx], category: newCategory };
    });
    updateAnnotations(newAnnotations);
    setHasChanges(true);
  };

  const handleConfidenceChange = (value) => {
    if (selectedAnnotation !== null) {
      const newAnnotations = [...localAnnotations];
      newAnnotations[selectedAnnotation] = {
        ...newAnnotations[selectedAnnotation],
        confidence: value,
      };
      updateAnnotations(newAnnotations);
      setHasChanges(true);
    }
  };

  const handleSaveChanges = async () => {
    try {
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
    resetHistory(annotations);
    setHasChanges(false);
    setSelectedAnnotation(null);
    setSelectedAnnotations([]);
  };

  const handleExportAnnotations = () => {
    const dataStr = JSON.stringify(localAnnotations, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `annotations_${imageId}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleConvertToPolygon = () => {
    if (selectedAnnotation === null) return;

    const ann = localAnnotations[selectedAnnotation];
    if (!ann.bbox || ann.type === 'polygon') return;

    const [x, y, w, h] = ann.bbox;
    const points = [
      [x, y],           // Top-left
      [x + w, y],       // Top-right
      [x + w, y + h],   // Bottom-right
      [x, y + h]        // Bottom-left
    ];

    const newAnnotations = [...localAnnotations];
    newAnnotations[selectedAnnotation] = {
      ...ann,
      type: 'polygon',
      points: points,
      bbox: undefined // Remove bbox
    };

    updateAnnotations(newAnnotations);
    setHasChanges(true);
  };

  const handleConvertToBbox = () => {
    if (selectedAnnotation === null) return;

    const ann = localAnnotations[selectedAnnotation];
    if (!ann.points || ann.type === 'bbox') return;

    // Calculate bounding box from polygon points
    const xs = ann.points.map(p => p[0]);
    const ys = ann.points.map(p => p[1]);
    const minX = Math.min(...xs);
    const minY = Math.min(...ys);
    const maxX = Math.max(...xs);
    const maxY = Math.max(...ys);

    const bbox = [minX, minY, maxX - minX, maxY - minY];

    const newAnnotations = [...localAnnotations];
    newAnnotations[selectedAnnotation] = {
      ...ann,
      type: 'bbox',
      bbox: bbox,
      points: undefined // Remove points
    };

    updateAnnotations(newAnnotations);
    setHasChanges(true);
  };

  const handleApplyTemplate = async (template) => {
    // Get canvas center position for new annotation
    const canvas = canvasRef.current;
    const img = imgRef.current;

    if (!canvas || !img) return;

    const scaleX = imageDimensions.width / img.clientWidth;
    const scaleY = imageDimensions.height / img.clientHeight;

    // Place template at canvas center
    const centerX = (canvas.width / 2) * scaleX;
    const centerY = (canvas.height / 2) * scaleY;

    let newAnnotation = {
      id: Date.now(),
      category: template.category,
      confidence: template.confidence,
      status: 'pending'
    };

    if (template.template_type === 'bbox' && template.bbox_data) {
      const width = template.bbox_data.width;
      const height = template.bbox_data.height;

      newAnnotation.bbox = [
        centerX - width / 2,
        centerY - height / 2,
        width,
        height
      ];
    } else if (template.template_type === 'polygon' && template.polygon_data) {
      newAnnotation.type = 'polygon';
      newAnnotation.points = template.polygon_data.points.map(([x, y]) => [
        centerX + x,
        centerY + y
      ]);
    }

    updateAnnotations([...localAnnotations, newAnnotation]);
    setHasChanges(true);
    setShowTemplateManager(false);

    // Increment usage count
    try {
      await incrementTemplateUsage(template.id);
    } catch (err) {
      console.error('Failed to increment template usage:', err);
    }
  };

  const handleSAMClick = async (e) => {
    if (!samMode) return;

    const pos = getMousePos(e);
    const img = imgRef.current;
    const scaleX = imageDimensions.width / img.clientWidth;
    const scaleY = imageDimensions.height / img.clientHeight;

    // Convert to original image coordinates
    const imageX = pos.x * scaleX;
    const imageY = pos.y * scaleY;

    // Add point with label (1 for foreground, 0 for background)
    const label = e.shiftKey ? 0 : 1;  // Shift+Click for background
    const newPoint = { x: imageX, y: imageY, label };

    const updatedPoints = [...samPoints, newPoint];
    setSamPoints(updatedPoints);

    // Generate mask after first point
    if (updatedPoints.length >= 1) {
      await generateSAMSegmentation(updatedPoints);
    }
  };

  const generateSAMSegmentation = async (points) => {
    setSamLoading(true);

    try {
      // Use mock SAM for now (replace with real SAM when configured)
      const result = await generateMockSAMMask(imageUrl, points);

      // Create polygon annotation from SAM result
      const newAnnotation = {
        id: Date.now(),
        type: 'polygon',
        points: result.polygon,
        category: selectedCategory,
        confidence: result.confidence,
        status: 'pending'
      };

      updateAnnotations([...localAnnotations, newAnnotation]);
      setHasChanges(true);

      // Reset SAM mode
      setSamMode(false);
      setSamPoints([]);

    } catch (err) {
      console.error('SAM generation failed:', err);
      alert('Failed to generate mask: ' + err.message);
    } finally {
      setSamLoading(false);
    }
  };

  return (
    <div className="relative">
      {/* Toolbar */}
      <div className="mb-4 bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          {/* Mode buttons */}
          <div className="flex space-x-2">
            <button
              onClick={() => { setMode('view'); setBatchMode(false); }}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                mode === 'view' && !batchMode
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              👁 View
            </button>
            <button
              onClick={() => { setMode('draw'); setBatchMode(false); }}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                mode === 'draw'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              ✏ Draw
            </button>
            <button
              onClick={() => { setBatchMode(!batchMode); setMode('view'); }}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                batchMode
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              ☑ Batch
            </button>
            <button
              onClick={() => {
                setSamMode(!samMode);
                setSamPoints([]);
                setMode('view');
                setBatchMode(false);
              }}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                samMode
                  ? 'bg-teal-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
              title="SAM Auto-Segmentation (Click object)"
            >
              🎯 SAM {samLoading && '⏳'}
            </button>
          </div>

          {/* Annotation Type Toggle */}
          {mode === 'draw' && (
            <div className="flex space-x-2">
              <button
                onClick={() => {
                  setAnnotationType('bbox');
                  setPolygonPoints([]);
                  setIsDrawingPolygon(false);
                }}
                className={`px-4 py-2 rounded font-medium transition-colors ${
                  annotationType === 'bbox'
                    ? 'bg-orange-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
                title="Rectangle (Bounding Box)"
              >
                ▭ Rectangle
              </button>
              <button
                onClick={() => {
                  setAnnotationType('polygon');
                  setCurrentBox(null);
                  setIsDrawing(false);
                }}
                className={`px-4 py-2 rounded font-medium transition-colors ${
                  annotationType === 'polygon'
                    ? 'bg-orange-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
                title="Polygon (Click points, click first point to close)"
              >
                ⬡ Polygon
              </button>
              {isDrawingPolygon && polygonPoints.length > 0 && (
                <button
                  onClick={() => {
                    setPolygonPoints([]);
                    setIsDrawingPolygon(false);
                  }}
                  className="px-4 py-2 bg-red-600 text-white rounded font-medium hover:bg-red-700"
                  title="Cancel polygon drawing"
                >
                  ✕ Cancel
                </button>
              )}
            </div>
          )}

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
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              <div
                className="w-6 h-6 rounded border-2 border-gray-300"
                style={{ backgroundColor: getCategoryColor(selectedCategory) }}
              />
            </div>
          )}

          {/* Confidence slider */}
          {mode === 'draw' && (
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Confidence:</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={confidenceValue}
                onChange={(e) => setConfidenceValue(parseFloat(e.target.value))}
                className="w-32"
              />
              <span className="text-sm text-gray-600 w-12">
                {(confidenceValue * 100).toFixed(0)}%
              </span>
            </div>
          )}

          {/* Selected annotation confidence adjustment */}
          {selectedAnnotation !== null && !batchMode && (
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Adjust:</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={localAnnotations[selectedAnnotation]?.confidence || 1}
                onChange={(e) => handleConfidenceChange(parseFloat(e.target.value))}
                className="w-32"
              />
              <span className="text-sm text-gray-600 w-12">
                {((localAnnotations[selectedAnnotation]?.confidence || 1) * 100).toFixed(0)}%
              </span>
            </div>
          )}

          {/* Batch operations */}
          {batchMode && selectedAnnotations.length > 0 && (
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700">
                {selectedAnnotations.length} selected
              </span>
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    handleBatchChangeCategory(e.target.value);
                    e.target.value = '';
                  }
                }}
                className="px-3 py-1 border border-gray-300 rounded text-sm"
              >
                <option value="">Change Category...</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              <button
                onClick={handleBatchDelete}
                className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
              >
                Delete All
              </button>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex space-x-2">
            {/* Undo/Redo */}
            <button
              onClick={undo}
              disabled={!canUndo}
              className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Undo (Ctrl+Z)"
            >
              ↶
            </button>
            <button
              onClick={redo}
              disabled={!canRedo}
              className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Redo (Ctrl+Y)"
            >
              ↷
            </button>

            {selectedAnnotation !== null && !batchMode && (
              <>
                <button
                  onClick={() => handleDeleteAnnotation(selectedAnnotation)}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 font-medium"
                >
                  🗑 Delete
                </button>

                {/* Conversion buttons */}
                {localAnnotations[selectedAnnotation]?.bbox && !localAnnotations[selectedAnnotation]?.type && (
                  <button
                    onClick={handleConvertToPolygon}
                    className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 font-medium"
                    title="Convert bounding box to polygon"
                  >
                    ⬡ To Polygon
                  </button>
                )}
                {localAnnotations[selectedAnnotation]?.type === 'polygon' && (
                  <button
                    onClick={handleConvertToBbox}
                    className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 font-medium"
                    title="Convert polygon to bounding box"
                  >
                    ▭ To BBox
                  </button>
                )}
              </>
            )}

            <button
              onClick={handleExportAnnotations}
              className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 font-medium"
            >
              📥 Export
            </button>

            <button
              onClick={() => setShowShortcuts(!showShortcuts)}
              className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 font-medium"
              title="Keyboard Shortcuts (Press ?)"
            >
              ⌨️ Shortcuts
            </button>

            <button
              onClick={() => setShowTemplateManager(true)}
              className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 font-medium"
              title="Annotation Templates"
            >
              📐 Templates
            </button>

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
          {mode === 'view' && !batchMode && !samMode && 'Click on annotations to select. Drag to move. Drag handles to resize (bbox only).'}
          {mode === 'draw' && annotationType === 'bbox' && 'Click and drag to draw a new bounding box.'}
          {mode === 'draw' && annotationType === 'polygon' && !isDrawingPolygon && 'Click points to draw a polygon. Click the first point (green) to close.'}
          {mode === 'draw' && annotationType === 'polygon' && isDrawingPolygon && `Drawing polygon (${polygonPoints.length} points). Click first point to finish.`}
          {batchMode && 'Click annotations to select/deselect. Use batch operations above.'}
          {samMode && !samLoading && 'Click on object to auto-segment (Shift+Click for background). SAM will generate polygon mask.'}
          {samMode && samLoading && 'Generating segmentation mask...'}
          {' | Keyboard: Ctrl+Z (undo), Ctrl+Y (redo), Delete (remove), Esc (cancel), Ctrl+D (draw), Ctrl+B (batch), Ctrl+A (select all)'}
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
              onClick={() => {
                if (batchMode) {
                  if (selectedAnnotations.includes(idx)) {
                    setSelectedAnnotations(selectedAnnotations.filter(i => i !== idx));
                  } else {
                    setSelectedAnnotations([...selectedAnnotations, idx]);
                  }
                } else {
                  setSelectedAnnotation(idx);
                }
              }}
              className={`flex items-center justify-between p-2 rounded cursor-pointer transition-colors ${
                selectedAnnotation === idx || selectedAnnotations.includes(idx)
                  ? 'bg-blue-100 border-2 border-blue-500'
                  : 'bg-white hover:bg-gray-100'
              }`}
            >
              <div className="flex items-center space-x-2">
                {batchMode && (
                  <input
                    type="checkbox"
                    checked={selectedAnnotations.includes(idx)}
                    onChange={() => {}}
                    className="w-4 h-4"
                  />
                )}
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

      {/* Keyboard Shortcuts Modal */}
      {showShortcuts && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setShowShortcuts(false)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              {/* Header */}
              <div className="flex justify-between items-center mb-6 border-b pb-4">
                <h2 className="text-2xl font-bold text-gray-900">⌨️ Keyboard Shortcuts</h2>
                <button
                  onClick={() => setShowShortcuts(false)}
                  className="text-gray-500 hover:text-gray-700 text-3xl leading-none"
                >
                  ×
                </button>
              </div>

              {/* Shortcuts Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* General */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <span className="mr-2">🎯</span> General
                  </h3>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Undo</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">Ctrl+Z</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Redo</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">Ctrl+Y</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Delete/Remove</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">Del / Backspace</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Cancel/Exit</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">Esc</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Save Changes</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">Ctrl+S</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Cycle Through Annotations</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">Tab</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Toggle Annotation Visibility</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">Space</kbd>
                    </div>
                  </div>
                </div>

                {/* Modes */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <span className="mr-2">🔄</span> Modes
                  </h3>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">View Mode</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">V</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Draw Mode</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">Ctrl+D</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Batch Mode</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">Ctrl+B</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Rectangle Tool</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">R</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Polygon Tool</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">P</kbd>
                    </div>
                  </div>
                </div>

                {/* Quick Category Selection */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <span className="mr-2">🏷️</span> Quick Category Selection
                  </h3>
                  <div className="space-y-2">
                    {categories.slice(0, 9).map((cat, idx) => (
                      <div key={cat} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span className="text-sm text-gray-700">{cat}</span>
                        <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">{idx + 1}</kbd>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Annotation Actions */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <span className="mr-2">✏️</span> Annotation Actions
                  </h3>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Copy Annotation</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">C</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Cut Annotation</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">X</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Paste Annotation</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">Ctrl+V</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Duplicate Selected</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">Ctrl+D</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Increase Confidence</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">+</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Decrease Confidence</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">-</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Select All (Batch Mode)</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">Ctrl+A</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Move Annotation (1px)</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">Arrow Keys</kbd>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">Move Annotation (10px)</span>
                      <kbd className="px-3 py-1 bg-gray-800 text-white text-xs rounded font-mono">Shift+Arrows</kbd>
                    </div>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="mt-6 pt-4 border-t">
                <p className="text-sm text-gray-600 text-center">
                  💡 Tip: Keyboard shortcuts work when not typing in input fields
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Template Manager Modal */}
      {showTemplateManager && (
        <TemplateManager
          onApplyTemplate={handleApplyTemplate}
          onClose={() => setShowTemplateManager(false)}
        />
      )}
    </div>
  );
}

export default AnnotationEditorV2;
