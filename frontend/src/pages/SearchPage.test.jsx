import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import SearchPage from './SearchPage';
import * as api from '../services/api';

vi.mock('../services/api');

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockSearchResults = {
  results: [
    {
      id: 'GDP',
      title: 'Gross Domestic Product',
      frequency: 'Quarterly',
      units: 'Billions of Dollars',
      seasonal_adjustment: 'Seasonally Adjusted',
      popularity: '93',
      last_updated: '2024-03-28',
    },
    {
      id: 'GDPPOT',
      title: 'Real Potential GDP',
      frequency: 'Quarterly',
      units: 'Billions of Chained 2009 Dollars',
      seasonal_adjustment: 'Not Seasonally Adjusted',
      popularity: '72',
      last_updated: '2024-02-04',
    },
  ],
  count: 2,
};

function renderSearchPage() {
  return render(
    <MemoryRouter>
      <SearchPage />
    </MemoryRouter>
  );
}

describe('SearchPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders search input and button', () => {
    renderSearchPage();
    expect(screen.getByRole('textbox', { name: /search query/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
  });

  it('displays search results in a table', async () => {
    api.searchSeries.mockResolvedValueOnce(mockSearchResults);
    renderSearchPage();

    const input = screen.getByRole('textbox', { name: /search query/i });
    fireEvent.change(input, { target: { value: 'gdp' } });
    fireEvent.click(screen.getByRole('button', { name: /search/i }));

    await waitFor(() => {
      expect(screen.getByText('GDP')).toBeInTheDocument();
    });

    expect(screen.getByText('Gross Domestic Product')).toBeInTheDocument();
    expect(screen.getByText('Real Potential GDP')).toBeInTheDocument();
    expect(screen.getByText('Found 2 results')).toBeInTheDocument();
  });

  it('navigates to detail page when clicking a result row', async () => {
    api.searchSeries.mockResolvedValueOnce(mockSearchResults);
    renderSearchPage();

    const input = screen.getByRole('textbox', { name: /search query/i });
    fireEvent.change(input, { target: { value: 'gdp' } });
    fireEvent.click(screen.getByRole('button', { name: /search/i }));

    await waitFor(() => {
      expect(screen.getByText('GDP')).toBeInTheDocument();
    });

    // Click the row containing GDP
    const gdpCell = screen.getByText('GDP');
    fireEvent.click(gdpCell.closest('tr'));

    expect(mockNavigate).toHaveBeenCalledWith('/series/GDP');
  });

  it('displays error message on search failure', async () => {
    api.searchSeries.mockRejectedValueOnce({
      response: { data: { detail: 'Search failed' } },
    });
    renderSearchPage();

    const input = screen.getByRole('textbox', { name: /search query/i });
    fireEvent.change(input, { target: { value: 'test' } });
    fireEvent.click(screen.getByRole('button', { name: /search/i }));

    await waitFor(() => {
      expect(screen.getByText('Search failed')).toBeInTheDocument();
    });
  });
});
