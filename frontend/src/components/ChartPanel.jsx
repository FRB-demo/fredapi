import React, { useMemo } from 'react'
import {
  ResponsiveContainer, ComposedChart, Line, Area, Bar,
  XAxis, YAxis, Tooltip, Legend, CartesianGrid, ReferenceLine,
} from 'recharts'
import { TrendingUp, BarChart3 } from 'lucide-react'

function mergeSeriesData(seriesList, forecasts) {
  const dateMap = {};

  seriesList.forEach(series => {
    (series.dates || []).forEach((date, i) => {
      if (!dateMap[date]) dateMap[date] = { date };
      dateMap[date][series.series_id] = series.values[i];
    });
  });

  forecasts.forEach(fc => {
    (fc.forecast_dates || []).forEach((date, i) => {
      if (!dateMap[date]) dateMap[date] = { date };
      dateMap[date][`${fc.series_id}_forecast`] = fc.forecast_values[i];
      if (fc.upper_bound) dateMap[date][`${fc.series_id}_upper`] = fc.upper_bound[i];
      if (fc.lower_bound) dateMap[date][`${fc.series_id}_lower`] = fc.lower_bound[i];
    });
  });

  return Object.values(dateMap).sort((a, b) => a.date.localeCompare(b.date));
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { year: '2-digit', month: 'short' });
}

function formatValue(val) {
  if (val === undefined || val === null) return '';
  if (Math.abs(val) >= 1e9) return (val / 1e9).toFixed(1) + 'B';
  if (Math.abs(val) >= 1e6) return (val / 1e6).toFixed(1) + 'M';
  if (Math.abs(val) >= 1e3) return (val / 1e3).toFixed(1) + 'K';
  return val.toFixed(2);
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-lg p-3 text-xs">
      <p className="font-medium text-slate-900 mb-1">
        {new Date(label + 'T00:00:00').toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
      </p>
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center gap-2 mt-0.5">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-slate-500">{entry.name}:</span>
          <span className="font-medium text-slate-900">{formatValue(entry.value)}</span>
        </div>
      ))}
    </div>
  );
}

export default function ChartPanel({ series, forecasts, chartType, dateRange }) {
  const chartData = useMemo(() => mergeSeriesData(series, forecasts), [series, forecasts]);

  // Find the boundary between historical and forecast data
  const lastHistoricalDate = useMemo(() => {
    let latest = '';
    series.forEach(s => {
      const dates = s.dates || [];
      if (dates.length > 0 && dates[dates.length - 1] > latest) {
        latest = dates[dates.length - 1];
      }
    });
    return latest;
  }, [series]);

  if (series.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-50">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <BarChart3 className="w-8 h-8 text-blue-500" />
          </div>
          <h2 className="text-xl font-semibold text-slate-900 mb-2">Welcome to EconSight</h2>
          <p className="text-slate-500 text-sm mb-6">
            Select economic indicators from the sidebar to start building your chart.
            Browse by category or search for specific FRED series.
          </p>
          <div className="grid grid-cols-2 gap-3 text-xs text-left">
            <div className="bg-white p-3 rounded-lg border border-slate-200">
              <div className="font-medium text-slate-700 mb-1">GDP & Growth</div>
              <div className="text-slate-400">GDP, GDPC1, Real GDP Growth</div>
            </div>
            <div className="bg-white p-3 rounded-lg border border-slate-200">
              <div className="font-medium text-slate-700 mb-1">Inflation</div>
              <div className="text-slate-400">CPI, Core CPI, PCE, Core PCE</div>
            </div>
            <div className="bg-white p-3 rounded-lg border border-slate-200">
              <div className="font-medium text-slate-700 mb-1">Labor Market</div>
              <div className="text-slate-400">Unemployment, Payrolls, Claims</div>
            </div>
            <div className="bg-white p-3 rounded-lg border border-slate-200">
              <div className="font-medium text-slate-700 mb-1">Interest Rates</div>
              <div className="text-slate-400">Fed Funds, 10Y Treasury, Spread</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Check if we have multiple Y-axis scales needed
  const useMultiAxis = series.length === 2 && series[0].units !== series[1].units;

  const renderSeries = (s, index) => {
    const yAxisId = useMultiAxis && index === 1 ? 'right' : 'left';

    const commonProps = {
      key: s.series_id,
      dataKey: s.series_id,
      name: `${s.series_id} - ${s.title}`,
      yAxisId,
    };

    if (chartType === 'area') {
      return (
        <Area
          {...commonProps}
          type="monotone"
          stroke={s.color}
          fill={s.color}
          fillOpacity={0.1}
          strokeWidth={2}
          dot={false}
          connectNulls
        />
      );
    }
    if (chartType === 'bar') {
      return (
        <Bar
          {...commonProps}
          fill={s.color}
          fillOpacity={0.8}
          radius={[2, 2, 0, 0]}
        />
      );
    }
    return (
      <Line
        {...commonProps}
        type="monotone"
        stroke={s.color}
        strokeWidth={2}
        dot={false}
        connectNulls
      />
    );
  };

  return (
    <div className="flex-1 flex flex-col bg-white m-4 rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Chart Header */}
      <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-slate-900">
            {series.length === 1 ? series[0].title : `${series.length} Series Comparison`}
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            {series.map(s => s.series_id).join(' | ')}
            {series[0]?.units ? ` | ${series[0].units}` : ''}
          </p>
        </div>
        {forecasts.length > 0 && (
          <div className="flex items-center gap-1.5 text-xs text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">
            <TrendingUp className="w-3.5 h-3.5" />
            Forecast Active
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="flex-1 p-4">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: useMultiAxis ? 60 : 20, bottom: 10, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              axisLine={{ stroke: '#e2e8f0' }}
              tickLine={false}
              minTickGap={50}
            />
            <YAxis
              yAxisId="left"
              tickFormatter={formatValue}
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              axisLine={false}
              tickLine={false}
              width={60}
            />
            {useMultiAxis && (
              <YAxis
                yAxisId="right"
                orientation="right"
                tickFormatter={formatValue}
                tick={{ fontSize: 11, fill: '#94a3b8' }}
                axisLine={false}
                tickLine={false}
                width={60}
              />
            )}
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }}
              iconType="line"
            />

            {/* Forecast reference line */}
            {forecasts.length > 0 && lastHistoricalDate && (
              <ReferenceLine
                x={lastHistoricalDate}
                yAxisId="left"
                stroke="#94a3b8"
                strokeDasharray="4 4"
                label={{ value: 'Forecast', position: 'top', fontSize: 10, fill: '#94a3b8' }}
              />
            )}

            {/* Historical series */}
            {series.map((s, i) => renderSeries(s, i))}

            {/* Forecast confidence bands */}
            {forecasts.map(fc => {
              const matchedSeries = series.find(s => s.series_id === fc.series_id);
              const matchedIndex = series.findIndex(s => s.series_id === fc.series_id);
              const color = matchedSeries?.color || '#94a3b8';
              const fcYAxisId = useMultiAxis && matchedIndex === 1 ? 'right' : 'left';
              return (
                <React.Fragment key={`forecast-${fc.series_id}`}>
                  <Area
                    dataKey={`${fc.series_id}_upper`}
                    name={`${fc.series_id} Upper`}
                    yAxisId={fcYAxisId}
                    type="monotone"
                    stroke="none"
                    fill={color}
                    fillOpacity={0.08}
                    connectNulls
                    legendType="none"
                  />
                  <Area
                    dataKey={`${fc.series_id}_lower`}
                    name={`${fc.series_id} Lower`}
                    yAxisId={fcYAxisId}
                    type="monotone"
                    stroke="none"
                    fill="#ffffff"
                    fillOpacity={1}
                    connectNulls
                    legendType="none"
                  />
                  <Line
                    dataKey={`${fc.series_id}_forecast`}
                    name={`${fc.series_id} Forecast (${fc.method})`}
                    yAxisId={fcYAxisId}
                    type="monotone"
                    stroke={color}
                    strokeWidth={2}
                    strokeDasharray="6 3"
                    dot={false}
                    connectNulls
                  />
                </React.Fragment>
              );
            })}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Stats bar */}
      {series.length > 0 && (
        <div className="px-5 py-2.5 bg-slate-50 border-t border-slate-100 flex gap-6 overflow-x-auto">
          {series.map(s => {
            const vals = s.values || [];
            const latest = vals[vals.length - 1];
            const prev = vals.length > 1 ? vals[vals.length - 2] : null;
            const change = prev !== null ? latest - prev : null;
            const pctChange = change !== null && prev !== 0 ? ((change / Math.abs(prev)) * 100) : null;

            return (
              <div key={s.series_id} className="flex items-center gap-4 text-xs flex-shrink-0">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: s.color }} />
                <div>
                  <span className="text-slate-500">{s.series_id}</span>
                  <span className="font-semibold text-slate-900 ml-2">{formatValue(latest)}</span>
                  {pctChange !== null && (
                    <span className={`ml-1.5 ${pctChange >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                      {pctChange >= 0 ? '+' : ''}{pctChange.toFixed(2)}%
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
