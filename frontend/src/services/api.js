const API_BASE = '/api';

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

export async function fetchSeries(seriesId, startDate, endDate) {
  let url = `/data/series/${seriesId}`;
  const params = new URLSearchParams();
  if (startDate) params.set('start_date', startDate);
  if (endDate) params.set('end_date', endDate);
  if (params.toString()) url += `?${params}`;
  return request(url);
}

export async function fetchMultiSeries(seriesList) {
  return request('/data/multi-series', {
    method: 'POST',
    body: JSON.stringify({ series: seriesList }),
  });
}

export async function searchSeries(query, limit = 20) {
  return request('/data/search', {
    method: 'POST',
    body: JSON.stringify({ query, limit }),
  });
}

export async function fetchPopularSeries() {
  return request('/data/popular');
}

export async function fetchCategories() {
  return request('/data/categories');
}

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

export async function sendChatMessage(message, context) {
  return request('/chat/', {
    method: 'POST',
    body: JSON.stringify({ message, context }),
  });
}

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

export async function listDatasets() {
  return request('/datasets/');
}

export async function getDatasetSeries(datasetId, dateCol, valueCol) {
  const params = new URLSearchParams({ date_col: dateCol, value_col: valueCol });
  return request(`/datasets/${datasetId}/series?${params}`);
}

export async function deleteDataset(datasetId) {
  return request(`/datasets/${datasetId}`, { method: 'DELETE' });
}
