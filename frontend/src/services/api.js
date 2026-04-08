import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

/**
 * Search for FRED series by text query.
 */
export async function searchSeries(query, { limit, orderBy, sortOrder } = {}) {
  const params = { q: query };
  if (limit) params.limit = limit;
  if (orderBy) params.order_by = orderBy;
  if (sortOrder) params.sort_order = sortOrder;
  const response = await api.get('/search', { params });
  return response.data;
}

/**
 * Get observations for a specific series.
 */
export async function getSeries(seriesId, { observationStart, observationEnd } = {}) {
  const params = {};
  if (observationStart) params.observation_start = observationStart;
  if (observationEnd) params.observation_end = observationEnd;
  const response = await api.get(`/series/${seriesId}`, { params });
  return response.data;
}

/**
 * Get metadata/info for a specific series.
 */
export async function getSeriesInfo(seriesId) {
  const response = await api.get(`/series/${seriesId}/info`);
  return response.data;
}

/**
 * Get all releases (revision history) for a specific series.
 */
export async function getSeriesReleases(seriesId) {
  const response = await api.get(`/series/${seriesId}/releases`);
  return response.data;
}

/**
 * Get vintage dates for a specific series.
 */
export async function getSeriesVintageDates(seriesId) {
  const response = await api.get(`/series/${seriesId}/vintage-dates`);
  return response.data;
}

/**
 * Get series data as known on a particular date.
 */
export async function getSeriesAsOf(seriesId, date) {
  const response = await api.get(`/series/${seriesId}/as-of`, {
    params: { date },
  });
  return response.data;
}
