import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getSeriesReleases, getSeriesInfo } from '../services/api';
import DataTable from '../components/DataTable';

const styles = {
  heading: {
    fontSize: 24,
    fontWeight: 700,
    color: '#003366',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#888',
    marginBottom: 16,
  },
  backLink: {
    display: 'inline-block',
    marginBottom: 16,
    color: '#003366',
    fontSize: 14,
  },
  error: {
    color: '#cc0000',
    marginBottom: 16,
  },
  loading: {
    color: '#666',
    padding: 24,
  },
  count: {
    color: '#666',
    marginBottom: 12,
    fontSize: 14,
  },
};

const releaseColumns = [
  { key: 'date', label: 'Observation Date' },
  { key: 'realtime_start', label: 'Release Date' },
  { key: 'value', label: 'Value' },
];

function RevisionHistoryPage() {
  const { id } = useParams();
  const [info, setInfo] = useState(null);
  const [releases, setReleases] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const [infoData, releasesData] = await Promise.all([
          getSeriesInfo(id),
          getSeriesReleases(id),
        ]);
        if (!cancelled) {
          setInfo(infoData);
          setReleases(releasesData.releases);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.response?.data?.detail || 'Failed to load revision history.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchData();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return <p style={styles.loading}>Loading revision history...</p>;
  }

  if (error) {
    return <p style={styles.error}>{error}</p>;
  }

  return (
    <div>
      <Link to={`/series/${id}`} style={styles.backLink}>
        &larr; Back to Series Detail
      </Link>

      <h1 style={styles.heading}>
        Revision History{info ? `: ${info.title}` : ''}
      </h1>
      <p style={styles.subtitle}>Series ID: {id}</p>

      {releases && (
        <>
          <p style={styles.count}>
            {releases.length} revision{releases.length !== 1 ? 's' : ''}
          </p>
          <DataTable columns={releaseColumns} data={releases} />
        </>
      )}
    </div>
  );
}

export default RevisionHistoryPage;
