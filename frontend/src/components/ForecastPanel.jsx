import React, { useState } from 'react'
import { TrendingUp, X, Play, Trash2 } from 'lucide-react'
import { runForecast } from '../services/api'

const METHODS = [
  { id: 'auto', label: 'Auto (Best Fit)', desc: 'Automatically selects the best method' },
  { id: 'holt_winters', label: 'Holt-Winters', desc: 'Best for seasonal patterns' },
  { id: 'arima', label: 'ARIMA(1,1,1)', desc: 'Best for stationary series' },
  { id: 'linear', label: 'Linear Trend', desc: 'Simple trend extrapolation' },
];

export default function ForecastPanel({ activeSeries, onAddForecast, forecasts, onRemoveForecast, onClose }) {
  const [selectedSeries, setSelectedSeries] = useState('');
  const [method, setMethod] = useState('auto');
  const [periods, setPeriods] = useState(12);
  const [confidence, setConfidence] = useState(0.95);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRunForecast = async () => {
    if (!selectedSeries) {
      setError('Please select a series');
      return;
    }
    setLoading(true);
    setError('');

    try {
      const result = await runForecast({
        seriesId: selectedSeries,
        periods,
        method,
        confidenceLevel: confidence,
      });
      onAddForecast(result);
    } catch (e) {
      setError(e.message || 'Forecast failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-emerald-500" />
          <h3 className="text-sm font-semibold text-slate-900">Forecasting</h3>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Series Selection */}
        <div>
          <label className="text-xs font-medium text-slate-500 uppercase tracking-wide">Series</label>
          <select
            value={selectedSeries}
            onChange={e => setSelectedSeries(e.target.value)}
            className="mt-1 w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">Select a series...</option>
            {activeSeries.map(s => (
              <option key={s.series_id} value={s.series_id}>
                {s.series_id} - {s.title}
              </option>
            ))}
          </select>
        </div>

        {/* Method Selection */}
        <div>
          <label className="text-xs font-medium text-slate-500 uppercase tracking-wide">Method</label>
          <div className="mt-1 space-y-1.5">
            {METHODS.map(m => (
              <button
                key={m.id}
                onClick={() => setMethod(m.id)}
                className={`w-full text-left p-2.5 rounded-lg border text-xs transition-all ${
                  method === m.id
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : 'border-slate-200 hover:bg-slate-50 text-slate-600'
                }`}
              >
                <div className="font-medium">{m.label}</div>
                <div className={method === m.id ? 'text-emerald-600' : 'text-slate-400'}>{m.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Periods */}
        <div>
          <label className="text-xs font-medium text-slate-500 uppercase tracking-wide">
            Forecast Horizon: {periods} periods
          </label>
          <input
            type="range"
            min="1"
            max="60"
            value={periods}
            onChange={e => setPeriods(parseInt(e.target.value))}
            className="mt-1 w-full accent-emerald-500"
          />
          <div className="flex justify-between text-xs text-slate-400 mt-0.5">
            <span>1</span>
            <span>60</span>
          </div>
        </div>

        {/* Confidence Level */}
        <div>
          <label className="text-xs font-medium text-slate-500 uppercase tracking-wide">
            Confidence: {(confidence * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0.80"
            max="0.99"
            step="0.01"
            value={confidence}
            onChange={e => setConfidence(parseFloat(e.target.value))}
            className="mt-1 w-full accent-emerald-500"
          />
          <div className="flex justify-between text-xs text-slate-400 mt-0.5">
            <span>80%</span>
            <span>99%</span>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="p-2.5 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
            {error}
          </div>
        )}

        {/* Run Button */}
        <button
          onClick={handleRunForecast}
          disabled={loading || !selectedSeries}
          className="w-full flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          {loading ? 'Running...' : 'Run Forecast'}
        </button>

        {/* Active Forecasts */}
        {forecasts.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Active Forecasts</h4>
            <div className="space-y-2">
              {forecasts.map(f => (
                <div key={f.series_id} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
                  <div className="text-xs">
                    <div className="font-medium text-slate-700">{f.series_id}</div>
                    <div className="text-slate-400">{f.method} | {f.forecast_dates?.length || 0} periods</div>
                  </div>
                  <button
                    onClick={() => onRemoveForecast(f.series_id)}
                    className="text-slate-400 hover:text-red-500 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
