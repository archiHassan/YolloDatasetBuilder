import { useState, useEffect } from 'react';
import {
  getTemplates,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  getTemplateCategories
} from '../api/client';

function TemplateManager({ onApplyTemplate, onClose }) {
  const [templates, setTemplates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'person',
    template_type: 'bbox',
    width: 100,
    height: 150,
    confidence: 0.9
  });

  useEffect(() => {
    loadTemplates();
    loadCategories();
  }, [selectedCategory, selectedType]);

  const loadTemplates = async () => {
    setLoading(true);
    setError(null);
    try {
      const category = selectedCategory === 'all' ? null : selectedCategory;
      const type = selectedType === 'all' ? null : selectedType;
      const data = await getTemplates(category, type);
      setTemplates(data);
    } catch (err) {
      setError('Failed to load templates: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await getTemplateCategories();
      setCategories(data.categories || []);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const handleCreateTemplate = async (e) => {
    e.preventDefault();

    const templateData = {
      name: formData.name,
      description: formData.description,
      category: formData.category,
      template_type: formData.template_type,
      confidence: formData.confidence,
      bbox_data: formData.template_type === 'bbox' ? {
        x: 0,
        y: 0,
        width: parseFloat(formData.width),
        height: parseFloat(formData.height),
        unit: 'absolute'
      } : null,
      polygon_data: null  // TODO: Add polygon template creation
    };

    try {
      if (editingTemplate) {
        await updateTemplate(editingTemplate.id, {
          name: formData.name,
          description: formData.description,
          category: formData.category,
          confidence: formData.confidence
        });
      } else {
        await createTemplate(templateData);
      }

      setShowCreateForm(false);
      setEditingTemplate(null);
      resetForm();
      loadTemplates();
    } catch (err) {
      setError('Failed to save template: ' + err.message);
    }
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!confirm('Are you sure you want to delete this template?')) return;

    try {
      await deleteTemplate(templateId);
      loadTemplates();
    } catch (err) {
      setError('Failed to delete template: ' + err.message);
    }
  };

  const handleEditTemplate = (template) => {
    setEditingTemplate(template);
    setFormData({
      name: template.name,
      description: template.description || '',
      category: template.category,
      template_type: template.template_type,
      width: template.bbox_data?.width || 100,
      height: template.bbox_data?.height || 150,
      confidence: template.confidence
    });
    setShowCreateForm(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      category: 'person',
      template_type: 'bbox',
      width: 100,
      height: 150,
      confidence: 0.9
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b flex justify-between items-center bg-gradient-to-r from-purple-600 to-indigo-600 text-white">
          <h2 className="text-2xl font-bold">📐 Annotation Templates</h2>
          <button
            onClick={onClose}
            className="text-white hover:bg-white hover:bg-opacity-20 rounded-full p-2 transition-colors"
          >
            <span className="text-3xl leading-none">×</span>
          </button>
        </div>

        {/* Toolbar */}
        <div className="p-4 border-b bg-gray-50">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-gray-700">Category:</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="all">All Categories</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>

              <label className="text-sm font-medium text-gray-700 ml-4">Type:</label>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="all">All Types</option>
                <option value="bbox">Bounding Box</option>
                <option value="polygon">Polygon</option>
              </select>
            </div>

            <button
              onClick={() => {
                setShowCreateForm(true);
                setEditingTemplate(null);
                resetForm();
              }}
              className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 font-medium transition-colors"
            >
              + New Template
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          {/* Create/Edit Form */}
          {showCreateForm && (
            <div className="mb-6 p-6 bg-blue-50 border-2 border-blue-300 rounded-lg">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                {editingTemplate ? 'Edit Template' : 'Create New Template'}
              </h3>
              <form onSubmit={handleCreateTemplate} className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                  <input
                    type="text"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
                    required
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
                    rows="2"
                  />
                </div>

                {!editingTemplate && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Type *</label>
                      <select
                        value={formData.template_type}
                        onChange={(e) => setFormData({ ...formData, template_type: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={editingTemplate}
                      >
                        <option value="bbox">Bounding Box</option>
                        <option value="polygon">Polygon</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Confidence</label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        value={formData.confidence}
                        onChange={(e) => setFormData({ ...formData, confidence: parseFloat(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>

                    {formData.template_type === 'bbox' && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Width (px)</label>
                          <input
                            type="number"
                            min="10"
                            value={formData.width}
                            onChange={(e) => setFormData({ ...formData, width: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
                            required
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Height (px)</label>
                          <input
                            type="number"
                            min="10"
                            value={formData.height}
                            onChange={(e) => setFormData({ ...formData, height: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
                            required
                          />
                        </div>
                      </>
                    )}
                  </>
                )}

                <div className="col-span-2 flex gap-2 justify-end">
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateForm(false);
                      setEditingTemplate(null);
                      resetForm();
                    }}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
                  >
                    {editingTemplate ? 'Update' : 'Create'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Templates Grid */}
          {loading ? (
            <div className="text-center py-8 text-gray-500">Loading templates...</div>
          ) : templates.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No templates found. Create your first template!
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {templates.map(template => (
                <div
                  key={template.id}
                  className="border-2 border-gray-200 rounded-lg p-4 hover:border-purple-400 hover:shadow-lg transition-all cursor-pointer"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <h4 className="font-bold text-gray-900 text-lg">{template.name}</h4>
                      <p className="text-xs text-gray-500 mt-1">{template.description}</p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      template.template_type === 'bbox' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                    }`}>
                      {template.template_type}
                    </span>
                  </div>

                  <div className="mb-3 text-sm space-y-1">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Category:</span>
                      <span className="font-medium text-gray-900">{template.category}</span>
                    </div>
                    {template.bbox_data && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Size:</span>
                        <span className="font-medium text-gray-900">
                          {template.bbox_data.width}×{template.bbox_data.height}px
                        </span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-gray-600">Confidence:</span>
                      <span className="font-medium text-gray-900">{(template.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Used:</span>
                      <span className="font-medium text-gray-900">{template.usage_count} times</span>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => onApplyTemplate && onApplyTemplate(template)}
                      className="flex-1 px-3 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 text-sm font-medium"
                    >
                      Apply
                    </button>
                    <button
                      onClick={() => handleEditTemplate(template)}
                      className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteTemplate(template.id)}
                      className="px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
                    >
                      Del
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default TemplateManager;
