import React, { useState, useEffect } from 'react'
import { Search, Plus, X, ChevronDown, ChevronRight, TrendingUp, Calendar, BarChart2, LineChart, AreaChart } from 'lucide-react'
import { fetchPopularSeries, fetchSeries, searchSeries } from '../services/api'

const CHART_TYPES = [
  { id: 'line', label: 'Line', icon: LineChart },
  { id: 'area', label: 'Area', icon: AreaChart },
  { id: 'bar', label: 'Bar', icon: BarChart2 },
];

export default function Sidebar({ onAddSeries, activeSeries, onRemoveSeries, dateRange, setDateRange, chartType, setChartType }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [popularSeries, setPopularSeries] = useState([]);
  const [categories, setCategories] = useState({});
  const [expandedCats, setExpandedCats] = useState({});
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [loadingSeries, setLoadingSeries] = useState(null);

  useEffect(() => {
    fetchPopularSeries().then(data => {
      setPopularSeries(data.series || []);
      // Group by category
      const cats = {};
      (data.series || []).forEach(s => {
        const cat = s.category || 'Other';
        if (!cats[cat]) cats[cat] = [];
        cats[cat].push(s);
      });
      setCategories(cats);
    }).catch(() => {});
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const data = await searchSeries(searchQuery);
      setSearchResults(data.results || []);
    } catch (e) {
      console.error('Search failed:', e);
    } finally {
      setSearching(false);
    }
  };

  const handleAddSeries = async (series) => {
    setLoadingSeries(series.series_id);
    try {
      const data = await fetchSeries(series.series_id, dateRange.start || undefined, dateRange.end || undefined);
      onAddSeries(data);
    } catch (e) {
      console.error('Failed to load series:', e);
    } finally {
      setLoadingSeries(null);
    }
  };

  const toggleCategory = (cat) => {
    setExpandedCats(prev => ({ ...prev, [cat]: !prev[cat] }));
  };

  const isActive = (seriesId) => activeSeries.some(s => s.series_id === seriesId);

  return (
    <aside className="w-72 bg-white border-r border-slate-200 flex flex-col overflow-hidden flex-shrink-0">
      {/* Search */}
      <div className="p-4 border-b border-slate-100">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="Search indicators..."
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        {searchQuery && (
          <button
            onClick={handleSearch}
            disabled={searching}
            className="mt-2 w-full py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {searching ? 'Searching...' : 'Search FRED'}
          </button>
        )}
      </div>

      {/* Chart Type & Date Range */}
      <div className="p-4 border-b border-slate-100 space-y-3">
        <div>
          <label className="text-xs font-medium text-slate-500 uppercase tracking-wide">Chart Type</label>
          <div className="flex gap-1 mt-1.5">
            {CHART_TYPES.map(ct => {
              const Icon = ct.icon;
              return (
                <button
                  key={ct.id}
                  onClick={() => setChartType(ct.id)}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                    chartType === ct.id
                      ? 'bg-blue-50 text-blue-700 border border-blue-200'
                      : 'text-slate-500 hover:bg-slate-50 border border-transparent'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {ct.label}
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-500 uppercase tracking-wide flex items-center gap-1">
            <Calendar className="w-3 h-3" /> Date Range
          </label>
          <div className="flex gap-2 mt-1.5">
            <input
              type="date"
              value={dateRange.start}
              onChange={e => setDateRange(prev => ({ ...prev, start: e.target.value }))}
              className="flex-1 px-2 py-1 bg-slate-50 border border-slate-200 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <input
              type="date"
              value={dateRange.end}
              onChange={e => setDateRange(prev => ({ ...prev, end: e.target.value }))}
              className="flex-1 px-2 py-1 bg-slate-50 border border-slate-200 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Active Series */}
      {activeSeries.length > 0 && (
        <div className="p-4 border-b border-slate-100">
          <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Active Series ({activeSeries.length})</h3>
          <div className="space-y-1.5">
            {activeSeries.map(s => (
              <div key={s.series_id} className="flex items-center gap-2 group">
                <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: s.color }} />
                <span className="text-xs text-slate-700 truncate flex-1" title={s.title}>
                  {s.series_id}
                </span>
                <button
                  onClick={() => onRemoveSeries(s.series_id)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="w-3.5 h-3.5 text-slate-400 hover:text-red-500" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search Results or Popular Series */}
      <div className="flex-1 overflow-y-auto p-4">
        {searchResults.length > 0 ? (
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide">Search Results</h3>
              <button onClick={() => { setSearchResults([]); setSearchQuery(''); }} className="text-xs text-slate-400 hover:text-slate-600">
                Clear
              </button>
            </div>
            <div className="space-y-1">
              {searchResults.map(s => (
                <button
                  key={s.series_id}
                  onClick={() => handleAddSeries(s)}
                  disabled={isActive(s.series_id) || loadingSeries === s.series_id}
                  className={`w-full text-left p-2 rounded-lg text-xs transition-all ${
                    isActive(s.series_id)
                      ? 'bg-blue-50 text-blue-700 cursor-default'
                      : 'hover:bg-slate-50 text-slate-700'
                  } ${loadingSeries === s.series_id ? 'opacity-50' : ''}`}
                >
                  <div className="font-medium flex items-center gap-1">
                    {loadingSeries === s.series_id ? (
                      <span className="animate-spin inline-block w-3 h-3 border border-blue-500 border-t-transparent rounded-full" />
                    ) : (
                      <Plus className="w-3 h-3 text-slate-400 flex-shrink-0" />
                    )}
                    {s.series_id}
                  </div>
                  <div className="text-slate-500 mt-0.5 truncate pl-4">{s.title}</div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div>
            <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Data Explorer</h3>
            {Object.entries(categories).map(([cat, items]) => (
              <div key={cat} className="mb-1">
                <button
                  onClick={() => toggleCategory(cat)}
                  className="w-full flex items-center gap-1.5 py-1.5 px-1 text-xs font-medium text-slate-600 hover:text-slate-900 transition-colors"
                >
                  {expandedCats[cat] ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                  {cat}
                  <span className="text-slate-400 ml-auto">{items.length}</span>
                </button>
                {expandedCats[cat] && (
                  <div className="ml-2 space-y-0.5">
                    {items.map(s => (
                      <button
                        key={s.series_id}
                        onClick={() => handleAddSeries(s)}
                        disabled={isActive(s.series_id) || loadingSeries === s.series_id}
                        className={`w-full text-left p-1.5 pl-4 rounded text-xs transition-all ${
                          isActive(s.series_id)
                            ? 'bg-blue-50 text-blue-600'
                            : 'hover:bg-slate-50 text-slate-600'
                        } ${loadingSeries === s.series_id ? 'opacity-50' : ''}`}
                      >
                        <span className="font-medium">{s.series_id}</span>
                        <span className="text-slate-400 ml-1.5">- {s.title}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
