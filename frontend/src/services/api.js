/**
 * EconSight API client — all backend communication goes through this module.
 * @module api
 */

const API_BASE = '/api';

/**
 * Generic fetch wrapper with error handling.
 * @param {string} url - Relative API path (appended to API_BASE).
 * @param {RequestInit} [options] - Fetch options.
 * @returns {Promise<Object>} Parsed JSON response.
 */
async function request(url, options = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

/**
 * Fetch a single FRED series by ID.
 * @param {string} seriesId - FRED series identifier (e.g. "GDP", "UNRATE").
 * @param {string} [startDate] - Optional start date (YYYY-MM-DD).
 * @param {string} [endDate] - Optional end date (YYYY-MM-DD).
 * @returns {Promise<{series_id: string, title: string, units: string, frequency: string, dates: string[], values: number[]}>}
 */
export async function fetchSeries(seriesId, startDate, endDate) {
  let url = `/data/series/${seriesId}`;
  const params = new URLSearchParams();
  if (startDate) params.set('start_date', startDate);
  if (endDate) params.set('end_date', endDate);
  if (params.toString()) url += `?${params}`;
  return request(url);
}

/**
 * Fetch multiple FRED series in one request.
 * @param {string[]} seriesList - Array of series IDs.
 * @returns {Promise<Object>}
 */
export async function fetchMultiSeries(seriesList) {
  return request('/data/multi-series', {
    method: 'POST',
    body: JSON.stringify({ series: seriesList }),
  });
}

/**
 * Search FRED series by keyword.
 * @param {string} query - Search term.
 * @param {number} [limit=20] - Max results.
 * @returns {Promise<{results: Array<{series_id: string, title: string, frequency: string, units: string}>}>}
 */
export async function searchSeries(query, limit = 20) {
  return request('/data/search', {
    method: 'POST',
    body: JSON.stringify({ query, limit }),
  });
}

/**
 * Fetch the curated list of popular economic series.
 * @returns {Promise<{series: Array<{series_id: string, title: string, category: string, frequency: string, units: string}>}>}
 */
export async function fetchPopularSeries() {
  return request('/data/popular');
}

/**
 * Fetch available series categories.
 * @returns {Promise<{categories: string[]}>}
 */
export async function fetchCategories() {
  return request('/data/categories');
}

/**
 * Run a forecast on a series.
 * @param {Object} params
 * @param {string} params.seriesId - Series to forecast.
 * @param {number} [params.periods=12] - Forecast horizon.
 * @param {string} [params.method='auto'] - Method: 'auto', 'holt_winters', 'arima', 'linear'.
 * @param {number} [params.confidenceLevel=0.95] - Confidence level for prediction intervals.
 * @param {string} [params.startDate] - Historical data start date.
 * @param {string} [params.endDate] - Historical data end date.
 * @returns {Promise<{method: string, forecast_dates: string[], forecast_values: number[], lower_bound: number[], upper_bound: number[]}>}
 */
export async function runForecast({ seriesId, periods, method, confidenceLevel, startDate, endDate }) {
  return request('/forecast/', {
    method: 'POST',
    body: JSON.stringify({
      series_id: seriesId,
      periods: periods || 12,
      method: method || 'auto',
      confidence_level: confidenceLevel || 0.95,
      start_date: startDate,
      end_date: endDate,
    }),
  });
}

/**
 * Send a chat message to the research assistant.
 * @param {string} message - User message.
 * @param {Array<{series_id: string, title: string, values: number[], dates: string[], units: string}>} [context] - Active series context.
 * @returns {Promise<{response: string, intent: string, suggested_series: Array<{series_id: string, title: string}>}>}
 */
export async function sendChatMessage(message, context) {
  return request('/chat/', {
    method: 'POST',
    body: JSON.stringify({ message, context }),
  });
}

/**
 * Upload a CSV or Excel file as a custom dataset.
 * @param {File} file - The file to upload.
 * @returns {Promise<{dataset_id: string, name: string, columns: string[], date_column: string|null, numeric_columns: string[], row_count: number, preview: Object[]}>}
 */
export async function uploadDataset(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/datasets/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

/**
 * List all uploaded datasets.
 * @returns {Promise<{datasets: Array<{dataset_id: string, name: string, columns: string[], row_count: number}>}>}
 */
export async function listDatasets() {
  return request('/datasets/');
}

/**
 * Extract a time series from a stored dataset.
 * @param {string} datasetId - Dataset identifier.
 * @param {string} dateCol - Column name to use as dates.
 * @param {string} valueCol - Column name to use as values.
 * @returns {Promise<{series_id: string, title: string, dates: string[], values: number[]}>}
 */
export async function getDatasetSeries(datasetId, dateCol, valueCol) {
  const params = new URLSearchParams({ date_col: dateCol, value_col: valueCol });
  return request(`/datasets/${datasetId}/series?${params}`);
}

/**
 * Delete an uploaded dataset.
 * @param {string} datasetId - Dataset identifier.
 * @returns {Promise<Object>}
 */
export async function deleteDataset(datasetId) {
  return request(`/datasets/${datasetId}`, { method: 'DELETE' });
}
