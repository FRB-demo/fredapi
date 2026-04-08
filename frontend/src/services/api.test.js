import { vi, describe, it, expect, beforeEach } from 'vitest';

const mockGet = vi.fn();

vi.mock('axios', () => ({
  default: {
    create: () => ({
      get: mockGet,
    }),
  },
}));

const {
  searchSeries,
  getSeries,
  getSeriesInfo,
  getSeriesReleases,
  getSeriesVintageDates,
  getSeriesAsOf,
} = await import('./api');

describe('API service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('searchSeries', () => {
    it('calls the search endpoint with query', async () => {
      const mockData = { results: [], count: 0 };
      mockGet.mockResolvedValueOnce({ data: mockData });

      const result = await searchSeries('gdp');

      expect(mockGet).toHaveBeenCalledWith('/search', {
        params: { q: 'gdp' },
      });
      expect(result).toEqual(mockData);
    });

    it('passes optional parameters', async () => {
      const mockData = { results: [], count: 0 };
      mockGet.mockResolvedValueOnce({ data: mockData });

      await searchSeries('gdp', { limit: 10, orderBy: 'popularity', sortOrder: 'desc' });

      expect(mockGet).toHaveBeenCalledWith('/search', {
        params: { q: 'gdp', limit: 10, order_by: 'popularity', sort_order: 'desc' },
      });
    });
  });

  describe('getSeries', () => {
    it('calls the series endpoint', async () => {
      const mockData = { series_id: 'GDP', observations: [] };
      mockGet.mockResolvedValueOnce({ data: mockData });

      const result = await getSeries('GDP');

      expect(mockGet).toHaveBeenCalledWith('/series/GDP', {
        params: {},
      });
      expect(result).toEqual(mockData);
    });

    it('passes date range parameters', async () => {
      const mockData = { series_id: 'GDP', observations: [] };
      mockGet.mockResolvedValueOnce({ data: mockData });

      await getSeries('GDP', {
        observationStart: '2024-01-01',
        observationEnd: '2024-12-31',
      });

      expect(mockGet).toHaveBeenCalledWith('/series/GDP', {
        params: {
          observation_start: '2024-01-01',
          observation_end: '2024-12-31',
        },
      });
    });
  });

  describe('getSeriesInfo', () => {
    it('calls the series info endpoint', async () => {
      const mockData = { id: 'GDP', title: 'Gross Domestic Product' };
      mockGet.mockResolvedValueOnce({ data: mockData });

      const result = await getSeriesInfo('GDP');

      expect(mockGet).toHaveBeenCalledWith('/series/GDP/info');
      expect(result).toEqual(mockData);
    });
  });

  describe('getSeriesReleases', () => {
    it('calls the series releases endpoint', async () => {
      const mockData = { series_id: 'GDP', releases: [] };
      mockGet.mockResolvedValueOnce({ data: mockData });

      const result = await getSeriesReleases('GDP');

      expect(mockGet).toHaveBeenCalledWith('/series/GDP/releases');
      expect(result).toEqual(mockData);
    });
  });

  describe('getSeriesVintageDates', () => {
    it('calls the vintage dates endpoint', async () => {
      const mockData = { series_id: 'GDP', vintage_dates: ['2024-01-30'] };
      mockGet.mockResolvedValueOnce({ data: mockData });

      const result = await getSeriesVintageDates('GDP');

      expect(mockGet).toHaveBeenCalledWith('/series/GDP/vintage-dates');
      expect(result).toEqual(mockData);
    });
  });

  describe('getSeriesAsOf', () => {
    it('calls the as-of endpoint with date', async () => {
      const mockData = { series_id: 'GDP', as_of_date: '2024-06-01', data: [] };
      mockGet.mockResolvedValueOnce({ data: mockData });

      const result = await getSeriesAsOf('GDP', '2024-06-01');

      expect(mockGet).toHaveBeenCalledWith('/series/GDP/as-of', {
        params: { date: '2024-06-01' },
      });
      expect(result).toEqual(mockData);
    });
  });
});
