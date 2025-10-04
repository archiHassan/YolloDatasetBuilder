import { useState, useEffect } from 'react';
import { getReviewStatistics, getExportStatistics, exportCOCO, exportYOLO, exportVOC } from '../api/client';

function Statistics() {
  const [stats, setStats] = useState(null);
  const [exportStats, setExportStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exportMessage, setExportMessage] = useState('');

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      const [reviewData, exportData] = await Promise.all([
        getReviewStatistics(),
        getExportStatistics().catch(() => null)
      ]);
      setStats(reviewData);
      setExportStats(exportData);
      setError(null);
    } catch (err) {
      setError('Failed to load statistics: ' + err.message);
      console.error('Error fetching statistics:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = (format) => {
    let url;
    let filename;

    switch (format) {
      case 'coco':
        url = exportCOCO();
        filename = 'annotations_coco.json';
        break;
      case 'yolo':
        url = exportYOLO();
        filename = 'yolo_export.zip';
        break;
      case 'voc':
        url = exportVOC();
        filename = 'voc_export.zip';
        break;
      default:
        return;
    }

    setExportMessage(`Downloading ${format.toUpperCase()} format...`);

    // Create temporary link and trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setTimeout(() => {
      setExportMessage(`${format.toUpperCase()} format downloaded successfully!`);
      setTimeout(() => setExportMessage(''), 3000);
    }, 500);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading statistics...</div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error || 'Failed to load statistics'}</p>
        <button
          onClick={fetchStatistics}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const StatCard = ({ title, value, color = 'blue', subtitle, icon }) => {
    const colorClasses = {
      blue: 'from-blue-500 to-blue-600',
      purple: 'from-purple-500 to-purple-600',
      green: 'from-green-500 to-green-600',
      red: 'from-red-500 to-red-600'
    };

    return (
      <div className="bg-white rounded-xl shadow-lg p-6 border-t-4 border-blue-400 hover:shadow-xl transition-shadow duration-300">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">{title}</h3>
          {icon && <div className={`w-10 h-10 bg-gradient-to-br ${colorClasses[color]} rounded-lg flex items-center justify-center shadow-md`}>
            {icon}
          </div>}
        </div>
        <p className={`text-5xl font-extrabold bg-gradient-to-r ${colorClasses[color]} bg-clip-text text-transparent mb-2`}>{value}</p>
        {subtitle && <p className="text-sm text-gray-600 font-medium">{subtitle}</p>}
      </div>
    );
  };

  const progressPercentage = stats.total_images > 0
    ? ((stats.reviewed / stats.total_images) * 100).toFixed(1)
    : 0;

  return (
    <div>
      {/* Header */}
      <div className="mb-8 bg-white rounded-2xl shadow-lg p-6 border-l-4 border-blue-600">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">📊 Dataset Statistics</h2>
            <p className="text-sm text-gray-600 font-medium">
              Overview of annotation review progress
            </p>
          </div>
          <button
            onClick={fetchStatistics}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 font-semibold shadow-lg hover:shadow-xl transition-all duration-200"
          >
            <svg className="w-5 h-5 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh Stats
          </button>
        </div>
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Images"
          value={stats.total_images}
          color="blue"
          subtitle="In dataset"
          icon={<svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>}
        />
        <StatCard
          title="Reviewed"
          value={stats.reviewed}
          color="purple"
          subtitle={`${progressPercentage}% complete`}
          icon={<svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>}
        />
        <StatCard
          title="Approved"
          value={stats.approved}
          color="green"
          subtitle={stats.total_images > 0 ? `${((stats.approved / stats.total_images) * 100).toFixed(1)}% of total` : ''}
          icon={<svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>}
        />
        <StatCard
          title="Rejected"
          value={stats.rejected}
          color="red"
          subtitle={stats.total_images > 0 ? `${((stats.rejected / stats.total_images) * 100).toFixed(1)}% of total` : ''}
          icon={<svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>}
        />
      </div>

      {/* Progress Bar */}
      <div className="bg-white rounded-2xl shadow-lg p-8 mb-8 border-t-4 border-purple-400">
        <h3 className="text-2xl font-bold text-gray-900 mb-6">
          📈 Review Progress
        </h3>
        <div className="relative pt-1">
          <div className="flex mb-4 items-center justify-between">
            <div>
              <span className="text-sm font-bold inline-block py-2 px-4 uppercase rounded-full text-white bg-gradient-to-r from-blue-600 to-blue-700 shadow-lg">
                {progressPercentage}% Complete
              </span>
            </div>
            <div className="text-right">
              <span className="text-sm font-semibold inline-block text-gray-700 bg-gray-100 px-4 py-2 rounded-full">
                {stats.pending} remaining
              </span>
            </div>
          </div>
          <div className="overflow-hidden h-6 text-xs flex rounded-full bg-gray-200 shadow-inner">
            <div
              style={{ width: `${progressPercentage}%` }}
              className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 transition-all duration-500 rounded-full"
            />
          </div>
        </div>

        <div className="mt-8 grid grid-cols-3 gap-6">
          <div className="text-center bg-gradient-to-br from-yellow-50 to-yellow-100 p-4 rounded-xl border-2 border-yellow-200">
            <p className="text-3xl font-extrabold text-yellow-600">{stats.pending}</p>
            <p className="text-sm text-gray-700 font-semibold mt-1">Pending</p>
          </div>
          <div className="text-center bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-xl border-2 border-green-200">
            <p className="text-3xl font-extrabold text-green-600">{stats.approved}</p>
            <p className="text-sm text-gray-700 font-semibold mt-1">Approved</p>
          </div>
          <div className="text-center bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-xl border-2 border-red-200">
            <p className="text-3xl font-extrabold text-red-600">{stats.rejected}</p>
            <p className="text-sm text-gray-700 font-semibold mt-1">Rejected</p>
          </div>
        </div>
      </div>

      {/* Approval Rate */}
      <div className="bg-white rounded-2xl shadow-lg p-8 mb-8 border-t-4 border-green-400">
        <h3 className="text-2xl font-bold text-gray-900 mb-6">
          ✓ Approval Rate
        </h3>
        <div className="flex items-center justify-center">
          <div className="relative bg-gradient-to-br from-green-50 to-blue-50 p-12 rounded-3xl border-4 border-green-200">
            <div className="text-7xl font-extrabold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              {stats.approval_rate.toFixed(1)}%
            </div>
            <p className="text-center text-sm text-gray-700 font-semibold mt-3">
              of reviewed images approved
            </p>
          </div>
        </div>
      </div>

      {/* Category Distribution Visualization */}
      {exportStats && exportStats.category_distribution && exportStats.category_distribution.length > 0 && (
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8 border-t-4 border-indigo-400">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            📊 Category Distribution
          </h3>

          {/* Bar Chart */}
          <div className="space-y-3 mb-6">
            {exportStats.category_distribution.map((cat, idx) => {
              const maxCount = Math.max(...exportStats.category_distribution.map(c => c.count));
              const percentage = maxCount > 0 ? (cat.count / maxCount * 100) : 0;
              const colors = [
                'bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-red-500',
                'bg-purple-500', 'bg-pink-500', 'bg-indigo-500', 'bg-orange-500'
              ];
              const color = colors[idx % colors.length];

              return (
                <div key={cat.id} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium text-gray-700">{cat.name}</span>
                    <span className="text-gray-600">{cat.count} annotations</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-6 overflow-hidden">
                    <div
                      className={`h-full ${color} transition-all duration-500 flex items-center justify-end px-2`}
                      style={{ width: `${percentage}%` }}
                    >
                      {percentage > 10 && (
                        <span className="text-xs text-white font-semibold">
                          {((cat.count / exportStats.total_annotations) * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">{exportStats.category_distribution.length}</p>
              <p className="text-xs text-gray-600">Categories</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">{exportStats.total_annotations}</p>
              <p className="text-xs text-gray-600">Total Annotations</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">
                {Math.max(...exportStats.category_distribution.map(c => c.count))}
              </p>
              <p className="text-xs text-gray-600">Most Frequent</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">
                {Math.min(...exportStats.category_distribution.map(c => c.count))}
              </p>
              <p className="text-xs text-gray-600">Least Frequent</p>
            </div>
          </div>
        </div>
      )}

      {/* Review Status Breakdown */}
      <div className="bg-white rounded-2xl shadow-lg p-8 mb-8 border-t-4 border-orange-400">
        <h3 className="text-2xl font-bold text-gray-900 mb-6">
          🔍 Review Status Breakdown
        </h3>

        {/* Donut Chart Simulation */}
        <div className="flex flex-col md:flex-row items-center gap-6">
          {/* Visual Representation */}
          <div className="flex-1 flex justify-center">
            <div className="relative w-48 h-48">
              {/* Pending Circle */}
              <div className="absolute inset-0 rounded-full" style={{
                background: `conic-gradient(
                  #fbbf24 0deg ${(stats.pending / stats.total_images * 360)}deg,
                  #10b981 ${(stats.pending / stats.total_images * 360)}deg ${((stats.pending + stats.approved) / stats.total_images * 360)}deg,
                  #ef4444 ${((stats.pending + stats.approved) / stats.total_images * 360)}deg 360deg
                )`
              }}></div>
              <div className="absolute inset-6 bg-white rounded-full flex items-center justify-center">
                <div className="text-center">
                  <p className="text-3xl font-bold text-gray-900">{stats.total_images}</p>
                  <p className="text-xs text-gray-600">Total Images</p>
                </div>
              </div>
            </div>
          </div>

          {/* Legend */}
          <div className="flex-1 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-4 h-4 bg-yellow-400 rounded"></div>
              <div className="flex-1">
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-700">Pending</span>
                  <span className="text-sm text-gray-600">{stats.pending}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                  <div
                    className="h-full bg-yellow-400 rounded-full transition-all duration-500"
                    style={{ width: `${(stats.pending / stats.total_images * 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-4 h-4 bg-green-500 rounded"></div>
              <div className="flex-1">
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-700">Approved</span>
                  <span className="text-sm text-gray-600">{stats.approved}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                  <div
                    className="h-full bg-green-500 rounded-full transition-all duration-500"
                    style={{ width: `${(stats.approved / stats.total_images * 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-4 h-4 bg-red-500 rounded"></div>
              <div className="flex-1">
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-700">Rejected</span>
                  <span className="text-sm text-gray-600">{stats.rejected}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                  <div
                    className="h-full bg-red-500 rounded-full transition-all duration-500"
                    style={{ width: `${(stats.rejected / stats.total_images * 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Export Section */}
      <div className="bg-white rounded-2xl shadow-lg p-8 border-t-4 border-teal-400">
        <h3 className="text-2xl font-bold text-gray-900 mb-6">
          📦 Export Dataset
        </h3>

        {exportMessage && (
          <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-blue-100 border-2 border-blue-300 rounded-xl shadow-md">
            <p className="text-blue-900 text-sm font-semibold">{exportMessage}</p>
          </div>
        )}

        {exportStats && (
          <div className="mb-8 grid grid-cols-3 gap-6 p-6 bg-gradient-to-br from-gray-50 to-blue-50 rounded-xl border-2 border-gray-200">
            <div className="text-center">
              <p className="text-3xl font-extrabold text-gray-900">{exportStats.total_images}</p>
              <p className="text-sm text-gray-600 font-semibold mt-1">Total Images</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-extrabold text-gray-900">{exportStats.total_annotations}</p>
              <p className="text-sm text-gray-600 font-semibold mt-1">Total Annotations</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-extrabold text-gray-900">{exportStats.avg_annotations_per_image.toFixed(1)}</p>
              <p className="text-sm text-gray-600 font-semibold mt-1">Avg per Image</p>
            </div>
          </div>
        )}

        <p className="text-sm text-gray-700 mb-6 font-medium">
          Export your annotated dataset in different formats for model training
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* COCO Export */}
          <div className="border-2 border-gray-200 rounded-xl p-6 hover:border-blue-500 hover:shadow-xl transition-all duration-200 bg-gradient-to-br from-white to-blue-50">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-bold text-gray-900 text-lg">COCO</h4>
              <span className="text-xs bg-blue-500 text-white px-3 py-1 rounded-full font-bold shadow-md">JSON</span>
            </div>
            <p className="text-sm text-gray-600 mb-6 leading-relaxed">
              Original COCO JSON format. Compatible with most frameworks.
            </p>
            <button
              onClick={() => handleExport('coco')}
              className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 text-sm font-bold shadow-lg hover:shadow-xl transition-all duration-200"
            >
              📥 Download COCO
            </button>
          </div>

          {/* YOLO Export */}
          <div className="border-2 border-gray-200 rounded-xl p-6 hover:border-green-500 hover:shadow-xl transition-all duration-200 bg-gradient-to-br from-white to-green-50">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-bold text-gray-900 text-lg">YOLO</h4>
              <span className="text-xs bg-green-500 text-white px-3 py-1 rounded-full font-bold shadow-md">ZIP</span>
            </div>
            <p className="text-sm text-gray-600 mb-6 leading-relaxed">
              YOLOv8 format with labels, classes, and data.yaml for training.
            </p>
            <button
              onClick={() => handleExport('yolo')}
              className="w-full px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-xl hover:from-green-700 hover:to-green-800 text-sm font-bold shadow-lg hover:shadow-xl transition-all duration-200"
            >
              📥 Download YOLO
            </button>
          </div>

          {/* VOC Export */}
          <div className="border-2 border-gray-200 rounded-xl p-6 hover:border-purple-500 hover:shadow-xl transition-all duration-200 bg-gradient-to-br from-white to-purple-50">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-bold text-gray-900 text-lg">Pascal VOC</h4>
              <span className="text-xs bg-purple-500 text-white px-3 py-1 rounded-full font-bold shadow-md">ZIP</span>
            </div>
            <p className="text-sm text-gray-600 mb-6 leading-relaxed">
              Pascal VOC XML format. Compatible with classical frameworks.
            </p>
            <button
              onClick={() => handleExport('voc')}
              className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-xl hover:from-purple-700 hover:to-purple-800 text-sm font-bold shadow-lg hover:shadow-xl transition-all duration-200"
            >
              📥 Download VOC
            </button>
          </div>
        </div>

        {/* Export Info */}
        <div className="mt-8 p-6 bg-gradient-to-br from-gray-50 to-blue-50 rounded-xl border-2 border-gray-200">
          <h5 className="text-base font-bold text-gray-900 mb-3">ℹ️ Export Information</h5>
          <ul className="text-sm text-gray-700 space-y-2 font-medium">
            <li className="flex items-start">
              <span className="text-blue-500 mr-2">•</span>
              <span><strong>COCO:</strong> Single JSON file with all annotations</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">•</span>
              <span><strong>YOLO:</strong> ZIP with labels/*.txt, classes.txt, and data.yaml</span>
            </li>
            <li className="flex items-start">
              <span className="text-purple-500 mr-2">•</span>
              <span><strong>VOC:</strong> ZIP with Annotations/*.xml files</span>
            </li>
            <li className="flex items-start">
              <span className="text-orange-500 mr-2">•</span>
              <span>All formats include README with usage instructions</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Statistics;
