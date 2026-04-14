import React, { useState, useEffect, useCallback } from 'react'
import { X, Upload, FileSpreadsheet, Trash2, Eye, Plus, Database } from 'lucide-react'
import { uploadDataset, listDatasets, getDatasetSeries, deleteDataset } from '../services/api'

export default function DatasetManager({ onAddSeries, onClose }) {
  const [datasets, setDatasets] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [selectedDateCol, setSelectedDateCol] = useState('');
  const [selectedValueCol, setSelectedValueCol] = useState('');
  const [dragOver, setDragOver] = useState(false);

  const loadDatasets = useCallback(async () => {
    try {
      const data = await listDatasets();
      setDatasets(data.datasets || []);
    } catch (e) {
      console.error('Failed to load datasets:', e);
    }
  }, []);

  useEffect(() => {
    loadDatasets();
  }, [loadDatasets]);

  const handleUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      const result = await uploadDataset(file);
      await loadDatasets();
      setSelectedDataset(result);
      if (result.date_column) setSelectedDateCol(result.date_column);
    } catch (e) {
      setError(e.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleFileInput = (e) => {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleUpload(file);
  };

  const handleAddToChart = async () => {
    if (!selectedDataset || !selectedDateCol || !selectedValueCol) return;
    try {
      const data = await getDatasetSeries(selectedDataset.dataset_id, selectedDateCol, selectedValueCol);
      onAddSeries(data);
    } catch (e) {
      setError(e.message || 'Failed to load series');
    }
  };

  const handleDelete = async (datasetId) => {
    try {
      await deleteDataset(datasetId);
      await loadDatasets();
      if (selectedDataset?.dataset_id === datasetId) {
        setSelectedDataset(null);
      }
    } catch (e) {
      console.error('Failed to delete dataset:', e);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-purple-500" />
            <h2 className="text-lg font-semibold text-slate-900">Dataset Manager</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-2 gap-6">
            {/* Left: Upload & List */}
            <div className="space-y-4">
              {/* Upload area */}
              <div
                className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors ${
                  dragOver ? 'border-purple-400 bg-purple-50' : 'border-slate-200 hover:border-slate-300'
                }`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
              >
                <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <p className="text-sm text-slate-600 mb-1">
                  Drop CSV or Excel file here
                </p>
                <p className="text-xs text-slate-400 mb-3">or click to browse</p>
                <label className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium cursor-pointer hover:bg-purple-700 transition-colors">
                  <FileSpreadsheet className="w-4 h-4" />
                  Choose File
                  <input
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    className="hidden"
                    onChange={handleFileInput}
                  />
                </label>
                {uploading && (
                  <div className="mt-3 flex items-center justify-center gap-2 text-sm text-purple-600">
                    <span className="animate-spin inline-block w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full" />
                    Uploading...
                  </div>
                )}
              </div>

              {/* Error */}
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                  {error}
                </div>
              )}

              {/* Datasets list */}
              <div>
                <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
                  Uploaded Datasets ({datasets.length})
                </h3>
                {datasets.length === 0 ? (
                  <p className="text-sm text-slate-400 text-center py-4">No datasets uploaded yet</p>
                ) : (
                  <div className="space-y-2">
                    {datasets.map(ds => (
                      <div
                        key={ds.dataset_id}
                        className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all ${
                          selectedDataset?.dataset_id === ds.dataset_id
                            ? 'border-purple-200 bg-purple-50'
                            : 'border-slate-200 hover:bg-slate-50'
                        }`}
                        onClick={() => {
                          setSelectedDataset(ds);
                          if (ds.date_column) setSelectedDateCol(ds.date_column);
                          setSelectedValueCol('');
                        }}
                      >
                        <div className="text-xs">
                          <div className="font-medium text-slate-700">{ds.name}</div>
                          <div className="text-slate-400 mt-0.5">
                            {ds.row_count} rows | {ds.columns.length} columns
                          </div>
                        </div>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDelete(ds.dataset_id); }}
                          className="text-slate-400 hover:text-red-500 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Right: Column selection & preview */}
            <div className="space-y-4">
              {selectedDataset ? (
                <>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 mb-3">
                      Configure: {selectedDataset.name}
                    </h3>

                    <div className="space-y-3">
                      <div>
                        <label className="text-xs font-medium text-slate-500">Date Column</label>
                        <select
                          value={selectedDateCol}
                          onChange={e => setSelectedDateCol(e.target.value)}
                          className="mt-1 w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          <option value="">Select date column...</option>
                          {selectedDataset.columns.map(col => (
                            <option key={col} value={col}>{col}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="text-xs font-medium text-slate-500">Value Column</label>
                        <select
                          value={selectedValueCol}
                          onChange={e => setSelectedValueCol(e.target.value)}
                          className="mt-1 w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          <option value="">Select value column...</option>
                          {(selectedDataset.numeric_columns || []).map(col => (
                            <option key={col} value={col}>{col}</option>
                          ))}
                        </select>
                      </div>

                      <button
                        onClick={handleAddToChart}
                        disabled={!selectedDateCol || !selectedValueCol}
                        className="w-full flex items-center justify-center gap-2 py-2.5 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        <Plus className="w-4 h-4" />
                        Add to Chart
                      </button>
                    </div>
                  </div>

                  {/* Data Preview */}
                  {selectedDataset.preview && (
                    <div>
                      <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                        <Eye className="w-3 h-3" /> Data Preview
                      </h4>
                      <div className="overflow-auto max-h-64 border border-slate-200 rounded-lg">
                        <table className="w-full text-xs">
                          <thead className="bg-slate-50 sticky top-0">
                            <tr>
                              {selectedDataset.columns.slice(0, 5).map(col => (
                                <th key={col} className="px-2 py-1.5 text-left text-slate-600 font-medium border-b border-slate-200">
                                  {col}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {selectedDataset.preview.slice(0, 10).map((row, i) => (
                              <tr key={i} className="border-b border-slate-100 last:border-0">
                                {selectedDataset.columns.slice(0, 5).map(col => (
                                  <td key={col} className="px-2 py-1 text-slate-600 truncate max-w-[120px]">
                                    {String(row[col] ?? '')}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex items-center justify-center h-full text-center">
                  <div>
                    <FileSpreadsheet className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                    <p className="text-sm text-slate-500">
                      Upload a dataset or select one from the list to configure it
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      Supports CSV, XLSX, and XLS files
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
