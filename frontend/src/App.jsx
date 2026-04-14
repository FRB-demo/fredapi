import React, { useState, useCallback } from 'react'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import ChartPanel from './components/ChartPanel'
import ChatPanel from './components/ChatPanel'
import DatasetManager from './components/DatasetManager'
import ForecastPanel from './components/ForecastPanel'

const CHART_COLORS = [
  '#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed',
  '#db2777', '#0891b2', '#65a30d', '#ea580c', '#6366f1',
];

export default function App() {
  const [activeSeries, setActiveSeries] = useState([]);
  const [chartType, setChartType] = useState('line');
  const [showChat, setShowChat] = useState(false);
  const [showDatasets, setShowDatasets] = useState(false);
  const [showForecast, setShowForecast] = useState(false);
  const [forecasts, setForecasts] = useState([]);
  const [dateRange, setDateRange] = useState({ start: '', end: '' });

  const addSeries = useCallback((series) => {
    setActiveSeries(prev => {
      if (prev.find(s => s.series_id === series.series_id)) return prev;
      const colorIdx = prev.length % CHART_COLORS.length;
      return [...prev, { ...series, color: CHART_COLORS[colorIdx] }];
    });
  }, []);

  const removeSeries = useCallback((seriesId) => {
    setActiveSeries(prev => prev.filter(s => s.series_id !== seriesId));
    setForecasts(prev => prev.filter(f => f.series_id !== seriesId));
  }, []);

  const addForecast = useCallback((forecast) => {
    setForecasts(prev => {
      const filtered = prev.filter(f => f.series_id !== forecast.series_id);
      return [...filtered, forecast];
    });
  }, []);

  const removeForecast = useCallback((seriesId) => {
    setForecasts(prev => prev.filter(f => f.series_id !== seriesId));
  }, []);

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      <Header
        showChat={showChat}
        setShowChat={setShowChat}
        showDatasets={showDatasets}
        setShowDatasets={setShowDatasets}
        showForecast={showForecast}
        setShowForecast={setShowForecast}
      />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          onAddSeries={addSeries}
          activeSeries={activeSeries}
          onRemoveSeries={removeSeries}
          dateRange={dateRange}
          setDateRange={setDateRange}
          chartType={chartType}
          setChartType={setChartType}
        />
        <main className="flex-1 flex overflow-hidden">
          <div className={`flex-1 flex flex-col overflow-hidden transition-all duration-300`}>
            <ChartPanel
              series={activeSeries}
              forecasts={forecasts}
              chartType={chartType}
              dateRange={dateRange}
            />
          </div>

          {showForecast && (
            <div className="w-80 border-l border-slate-200 bg-white overflow-y-auto">
              <ForecastPanel
                activeSeries={activeSeries}
                onAddForecast={addForecast}
                forecasts={forecasts}
                onRemoveForecast={removeForecast}
                onClose={() => setShowForecast(false)}
              />
            </div>
          )}

          {showChat && (
            <div className="w-96 border-l border-slate-200 bg-white overflow-hidden flex flex-col">
              <ChatPanel
                activeSeries={activeSeries}
                onAddSeries={addSeries}
                onClose={() => setShowChat(false)}
              />
            </div>
          )}
        </main>
      </div>

      {showDatasets && (
        <DatasetManager
          onAddSeries={addSeries}
          onClose={() => setShowDatasets(false)}
        />
      )}
    </div>
  );
}
