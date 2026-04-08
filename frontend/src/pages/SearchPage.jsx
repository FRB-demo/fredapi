import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchSeries } from '../services/api';
import DataTable from '../components/DataTable';

const styles = {
  container: {
    maxWidth: 960,
  },
  heading: {
    fontSize: 28,
    fontWeight: 700,
    marginBottom: 8,
    color: '#003366',
  },
  subtitle: {
    color: '#555',
    marginBottom: 24,
  },
  form: {
    display: 'flex',
    gap: 8,
    marginBottom: 24,
  },
  input: {
    flex: 1,
    padding: '10px 14px',
    border: '1px solid #ccc',
    borderRadius: 4,
    fontSize: 16,
  },
  button: {
    padding: '10px 24px',
    backgroundColor: '#003366',
    color: '#fff',
    border: 'none',
    borderRadius: 4,
    fontSize: 16,
    cursor: 'pointer',
  },
  error: {
    color: '#cc0000',
    marginBottom: 16,
  },
  info: {
    color: '#666',
    marginBottom: 16,
  },
};

const searchColumns = [
  { key: 'id', label: 'Series ID' },
  { key: 'title', label: 'Title' },
  { key: 'frequency', label: 'Frequency' },
  { key: 'units', label: 'Units' },
  { key: 'seasonal_adjustment', label: 'Seasonal Adj.' },
  { key: 'popularity', label: 'Popularity' },
  { key: 'last_updated', label: 'Last Updated' },
];

function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const data = await searchSeries(query.trim());
      setResults(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred while searching.');
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRowClick = (row) => {
    navigate(`/series/${row.id}`);
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.heading}>Search FRED Data</h1>
      <p style={styles.subtitle}>
        Search for economic data series from the Federal Reserve Economic Data (FRED) database.
      </p>

      <form onSubmit={handleSearch} style={styles.form}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for series (e.g., GDP, unemployment, inflation)..."
          style={styles.input}
          aria-label="Search query"
        />
        <button type="submit" style={styles.button} disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <p style={styles.error}>{error}</p>}

      {results && (
        <>
          <p style={styles.info}>
            Found {results.count} result{results.count !== 1 ? 's' : ''}
          </p>
          <DataTable
            columns={searchColumns}
            data={results.results}
            onRowClick={handleRowClick}
          />
        </>
      )}
    </div>
  );
}

export default SearchPage;
