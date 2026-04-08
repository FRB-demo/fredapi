import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getSeries, getSeriesInfo } from '../services/api';
import SeriesChart from '../components/SeriesChart';
import DataTable from '../components/DataTable';

const styles = {
  heading: {
    fontSize: 24,
    fontWeight: 700,
    color: '#003366',
    marginBottom: 4,
  },
  seriesId: {
    fontSize: 14,
    color: '#888',
    marginBottom: 16,
  },
  metadataGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
    gap: 12,
    marginBottom: 24,
    padding: 16,
    backgroundColor: '#fff',
    borderRadius: 8,
    border: '1px solid #e0e0e0',
  },
  metaItem: {
    fontSize: 13,
  },
  metaLabel: {
    fontWeight: 600,
    color: '#003366',
    marginBottom: 2,
  },
  metaValue: {
    color: '#333',
  },
  notes: {
    gridColumn: '1 / -1',
    fontSize: 13,
    color: '#555',
    lineHeight: 1.5,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 600,
    color: '#003366',
    marginBottom: 12,
  },
  filterRow: {
    display: 'flex',
    gap: 12,
    alignItems: 'flex-end',
    marginBottom: 16,
    flexWrap: 'wrap',
  },
  filterGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  filterLabel: {
    fontSize: 12,
    fontWeight: 600,
    color: '#666',
  },
  filterInput: {
    padding: '6px 10px',
    border: '1px solid #ccc',
    borderRadius: 4,
    fontSize: 14,
  },
  filterButton: {
    padding: '6px 16px',
    backgroundColor: '#003366',
    color: '#fff',
    border: 'none',
    borderRadius: 4,
    cursor: 'pointer',
    fontSize: 14,
  },
  link: {
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
};

const observationColumns = [
  { key: 'date', label: 'Date' },
  { key: 'value', label: 'Value' },
];

function SeriesDetailPage() {
  const { id } = useParams();
  const [info, setInfo] = useState(null);
  const [observations, setObservations] = useState(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const [infoData, seriesData] = await Promise.all([
          getSeriesInfo(id),
          getSeries(id),
        ]);
        if (!cancelled) {
          setInfo(infoData);
          setObservations(seriesData.observations);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.response?.data?.detail || 'Failed to load series data.');
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

  const handleFilter = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (startDate) params.observationStart = startDate;
      if (endDate) params.observationEnd = endDate;
      const seriesData = await getSeries(id, params);
      setObservations(seriesData.observations);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to filter data.');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !info) {
    return <p style={styles.loading}>Loading series data...</p>;
  }

  if (error && !info) {
    return <p style={styles.error}>{error}</p>;
  }

  return (
    <div>
      {info && (
        <>
          <h1 style={styles.heading}>{info.title}</h1>
          <p style={styles.seriesId}>Series ID: {id}</p>

          <div style={styles.metadataGrid}>
            <div style={styles.metaItem}>
              <div style={styles.metaLabel}>Units</div>
              <div style={styles.metaValue}>{info.units}</div>
            </div>
            <div style={styles.metaItem}>
              <div style={styles.metaLabel}>Frequency</div>
              <div style={styles.metaValue}>{info.frequency}</div>
            </div>
            <div style={styles.metaItem}>
              <div style={styles.metaLabel}>Seasonal Adjustment</div>
              <div style={styles.metaValue}>{info.seasonal_adjustment}</div>
            </div>
            <div style={styles.metaItem}>
              <div style={styles.metaLabel}>Observation Start</div>
              <div style={styles.metaValue}>{info.observation_start}</div>
            </div>
            <div style={styles.metaItem}>
              <div style={styles.metaLabel}>Observation End</div>
              <div style={styles.metaValue}>{info.observation_end}</div>
            </div>
            <div style={styles.metaItem}>
              <div style={styles.metaLabel}>Last Updated</div>
              <div style={styles.metaValue}>{info.last_updated}</div>
            </div>
            {info.notes && (
              <div style={styles.notes}>
                <div style={styles.metaLabel}>Notes</div>
                <div>{info.notes}</div>
              </div>
            )}
          </div>

          <Link to={`/series/${id}/revisions`} style={styles.link}>
            View Revision History
          </Link>
        </>
      )}

      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Observations</h2>

        <div style={styles.filterRow}>
          <div style={styles.filterGroup}>
            <label style={styles.filterLabel} htmlFor="start-date">Start Date</label>
            <input
              id="start-date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              style={styles.filterInput}
            />
          </div>
          <div style={styles.filterGroup}>
            <label style={styles.filterLabel} htmlFor="end-date">End Date</label>
            <input
              id="end-date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              style={styles.filterInput}
            />
          </div>
          <button onClick={handleFilter} style={styles.filterButton}>
            Apply Filter
          </button>
        </div>

        {observations && <SeriesChart data={observations} />}

        {error && <p style={styles.error}>{error}</p>}

        {observations && (
          <DataTable columns={observationColumns} data={observations} />
        )}
      </div>
    </div>
  );
}

export default SeriesDetailPage;
