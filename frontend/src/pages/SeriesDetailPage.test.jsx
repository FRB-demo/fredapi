import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';
import SeriesDetailPage from './SeriesDetailPage';
import * as api from '../services/api';

vi.mock('../services/api');

// Mock recharts to avoid rendering issues in tests
vi.mock('recharts', () => ({
  LineChart: ({ children }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  ResponsiveContainer: ({ children }) => <div>{children}</div>,
}));

const mockInfo = {
  id: 'GDP',
  title: 'Gross Domestic Product',
  units: 'Billions of Dollars',
  frequency: 'Quarterly',
  seasonal_adjustment: 'Seasonally Adjusted',
  observation_start: '1947-01-01',
  observation_end: '2024-01-01',
  last_updated: '2024-03-28',
  notes: 'GDP measures the value of goods and services.',
};

const mockSeries = {
  series_id: 'GDP',
  observations: [
    { date: '2023-10-01', value: 27610.1 },
    { date: '2024-01-01', value: 27956.0 },
  ],
};

function renderSeriesDetailPage(seriesId = 'GDP') {
  return render(
    <MemoryRouter initialEntries={[`/series/${seriesId}`]}>
      <Routes>
        <Route path="/series/:id" element={<SeriesDetailPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('SeriesDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders series metadata', async () => {
    api.getSeriesInfo.mockResolvedValueOnce(mockInfo);
    api.getSeries.mockResolvedValueOnce(mockSeries);
    renderSeriesDetailPage();

    await waitFor(() => {
      expect(screen.getByText('Gross Domestic Product')).toBeInTheDocument();
    });

    expect(screen.getByText('Billions of Dollars')).toBeInTheDocument();
    expect(screen.getByText('Quarterly')).toBeInTheDocument();
    expect(screen.getByText('Seasonally Adjusted')).toBeInTheDocument();
  });

  it('renders chart with mock data', async () => {
    api.getSeriesInfo.mockResolvedValueOnce(mockInfo);
    api.getSeries.mockResolvedValueOnce(mockSeries);
    renderSeriesDetailPage();

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

  it('renders observations table', async () => {
    api.getSeriesInfo.mockResolvedValueOnce(mockInfo);
    api.getSeries.mockResolvedValueOnce(mockSeries);
    renderSeriesDetailPage();

    await waitFor(() => {
      expect(screen.getByText('2023-10-01')).toBeInTheDocument();
    });

    expect(screen.getByText('27610.1')).toBeInTheDocument();
    expect(screen.getByText('27956')).toBeInTheDocument();
  });

  it('applies date range filter', async () => {
    api.getSeriesInfo.mockResolvedValueOnce(mockInfo);
    api.getSeries
      .mockResolvedValueOnce(mockSeries)
      .mockResolvedValueOnce({
        series_id: 'GDP',
        observations: [{ date: '2024-01-01', value: 27956.0 }],
      });

    renderSeriesDetailPage();

    await waitFor(() => {
      expect(screen.getByText('Gross Domestic Product')).toBeInTheDocument();
    });

    const startInput = screen.getByLabelText('Start Date');
    const endInput = screen.getByLabelText('End Date');

    fireEvent.change(startInput, { target: { value: '2024-01-01' } });
    fireEvent.change(endInput, { target: { value: '2024-12-31' } });
    fireEvent.click(screen.getByText('Apply Filter'));

    await waitFor(() => {
      expect(api.getSeries).toHaveBeenCalledTimes(2);
    });

    expect(api.getSeries).toHaveBeenLastCalledWith('GDP', {
      observationStart: '2024-01-01',
      observationEnd: '2024-12-31',
    });
  });

  it('shows error on load failure', async () => {
    api.getSeriesInfo.mockRejectedValueOnce({
      response: { data: { detail: 'Series not found' } },
    });
    api.getSeries.mockRejectedValueOnce({
      response: { data: { detail: 'Series not found' } },
    });
    renderSeriesDetailPage('INVALID');

    await waitFor(() => {
      expect(screen.getByText('Series not found')).toBeInTheDocument();
    });
  });

  it('has link to revision history', async () => {
    api.getSeriesInfo.mockResolvedValueOnce(mockInfo);
    api.getSeries.mockResolvedValueOnce(mockSeries);
    renderSeriesDetailPage();

    await waitFor(() => {
      expect(screen.getByText('View Revision History')).toBeInTheDocument();
    });

    const link = screen.getByText('View Revision History');
    expect(link.getAttribute('href')).toBe('/series/GDP/revisions');
  });
});
