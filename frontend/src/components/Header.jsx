import React from 'react'
import { BarChart3, MessageSquare, Database, TrendingUp } from 'lucide-react'

export default function Header({ showChat, setShowChat, showDatasets, setShowDatasets, showForecast, setShowForecast }) {
  return (
    <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between flex-shrink-0">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center">
          <BarChart3 className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-slate-900 leading-tight">EconSight</h1>
          <p className="text-xs text-slate-500">Economic Research & Forecasting Platform</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => setShowForecast(v => !v)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            showForecast
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              : 'text-slate-600 hover:bg-slate-100 border border-transparent'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          Forecast
        </button>

        <button
          onClick={() => setShowDatasets(v => !v)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            showDatasets
              ? 'bg-purple-50 text-purple-700 border border-purple-200'
              : 'text-slate-600 hover:bg-slate-100 border border-transparent'
          }`}
        >
          <Database className="w-4 h-4" />
          Datasets
        </button>

        <button
          onClick={() => setShowChat(v => !v)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            showChat
              ? 'bg-blue-50 text-blue-700 border border-blue-200'
              : 'text-slate-600 hover:bg-slate-100 border border-transparent'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          Chat
        </button>
      </div>
    </header>
  );
}
