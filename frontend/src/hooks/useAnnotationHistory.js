import { useState, useCallback } from 'react';

/**
 * Custom hook for managing annotation history with undo/redo
 */
export function useAnnotationHistory(initialAnnotations = []) {
  const [annotations, setAnnotations] = useState(initialAnnotations);
  const [history, setHistory] = useState([initialAnnotations]);
  const [currentIndex, setCurrentIndex] = useState(0);

  // Update annotations and add to history
  const updateAnnotations = useCallback((newAnnotations) => {
    // Remove any future history beyond current index
    const newHistory = history.slice(0, currentIndex + 1);

    // Add new state to history
    newHistory.push(newAnnotations);

    // Limit history to last 50 states to prevent memory issues
    const limitedHistory = newHistory.slice(-50);

    setHistory(limitedHistory);
    setCurrentIndex(limitedHistory.length - 1);
    setAnnotations(newAnnotations);
  }, [history, currentIndex]);

  // Undo to previous state
  const undo = useCallback(() => {
    if (currentIndex > 0) {
      const newIndex = currentIndex - 1;
      setCurrentIndex(newIndex);
      setAnnotations(history[newIndex]);
      return true;
    }
    return false;
  }, [currentIndex, history]);

  // Redo to next state
  const redo = useCallback(() => {
    if (currentIndex < history.length - 1) {
      const newIndex = currentIndex + 1;
      setCurrentIndex(newIndex);
      setAnnotations(history[newIndex]);
      return true;
    }
    return false;
  }, [currentIndex, history]);

  // Reset history with new initial state
  const resetHistory = useCallback((newAnnotations) => {
    setAnnotations(newAnnotations);
    setHistory([newAnnotations]);
    setCurrentIndex(0);
  }, []);

  const canUndo = currentIndex > 0;
  const canRedo = currentIndex < history.length - 1;

  return {
    annotations,
    updateAnnotations,
    undo,
    redo,
    canUndo,
    canRedo,
    resetHistory,
  };
}
