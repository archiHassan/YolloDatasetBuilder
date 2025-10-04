import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Images API
export const getImages = async (skip = 0, limit = 20) => {
  const response = await apiClient.get('/api/images/', { params: { skip, limit } });
  return response.data;
};

export const getImage = async (id) => {
  const response = await apiClient.get(`/api/images/${id}`);
  return response.data;
};

export const getImageUrl = (filename) => {
  return `${API_BASE_URL}/static/images/${filename}`;
};

// Annotations API
export const getAnnotations = async (imageId) => {
  const response = await apiClient.get(`/api/annotations/${imageId}`);
  return response.data;
};

export const createAnnotation = async (annotation) => {
  const response = await apiClient.post('/api/annotations/', annotation);
  return response.data;
};

export const updateAnnotation = async (id, annotation) => {
  const response = await apiClient.put(`/api/annotations/${id}`, annotation);
  return response.data;
};

export const deleteAnnotation = async (id) => {
  const response = await apiClient.delete(`/api/annotations/${id}`);
  return response.data;
};

// Review API
export const getReviewQueue = async (limit = 10) => {
  const response = await apiClient.get('/api/review/queue', { params: { limit } });
  return response.data;
};

export const approveImage = async (imageId) => {
  const response = await apiClient.post(`/api/review/${imageId}/approve`);
  return response.data;
};

export const rejectImage = async (imageId, reason = '') => {
  const response = await apiClient.post(`/api/review/${imageId}/reject`, { reason });
  return response.data;
};

export const getReviewStatistics = async () => {
  const response = await apiClient.get('/api/review/statistics');
  return response.data;
};

// Export API
export const getExportFormats = async () => {
  const response = await apiClient.get('/api/export/formats');
  return response.data;
};

export const getExportStatistics = async () => {
  const response = await apiClient.get('/api/export/statistics');
  return response.data;
};

export const exportCOCO = (split = 'all') => {
  return `${API_BASE_URL}/api/export/coco?split=${split}`;
};

export const exportYOLO = () => {
  return `${API_BASE_URL}/api/export/yolo`;
};

export const exportVOC = () => {
  return `${API_BASE_URL}/api/export/voc`;
};

// Templates API
export const getTemplates = async (category = null, templateType = null) => {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (templateType) params.append('template_type', templateType);

  const response = await apiClient.get(`/api/templates?${params.toString()}`);
  return response.data;
};

export const getTemplate = async (templateId) => {
  const response = await apiClient.get(`/api/templates/${templateId}`);
  return response.data;
};

export const createTemplate = async (templateData) => {
  const response = await apiClient.post('/api/templates', templateData);
  return response.data;
};

export const updateTemplate = async (templateId, templateData) => {
  const response = await apiClient.put(`/api/templates/${templateId}`, templateData);
  return response.data;
};

export const deleteTemplate = async (templateId) => {
  const response = await apiClient.delete(`/api/templates/${templateId}`);
  return response.data;
};

export const incrementTemplateUsage = async (templateId) => {
  const response = await apiClient.post(`/api/templates/${templateId}/use`);
  return response.data;
};

export const getTemplateCategories = async () => {
  const response = await apiClient.get('/api/templates/categories/list');
  return response.data;
};

// SAM API
export const generateSAMMask = async (imagePath, points, box = null) => {
  const response = await apiClient.post('/api/sam/generate', {
    image_path: imagePath,
    points: points,
    box: box
  });
  return response.data;
};

export const generateMockSAMMask = async (imagePath, points) => {
  const response = await apiClient.post('/api/sam/generate-mock', {
    image_path: imagePath,
    points: points
  });
  return response.data;
};

export const getSAMStatus = async () => {
  const response = await apiClient.get('/api/sam/status');
  return response.data;
};

export default apiClient;
