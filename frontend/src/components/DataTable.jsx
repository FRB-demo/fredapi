const styles = {
  container: {
    overflowX: 'auto',
    marginTop: 16,
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: 14,
  },
  th: {
    textAlign: 'left',
    padding: '10px 12px',
    borderBottom: '2px solid #003366',
    backgroundColor: '#f0f4f8',
    fontWeight: 600,
    color: '#003366',
    whiteSpace: 'nowrap',
  },
  td: {
    padding: '8px 12px',
    borderBottom: '1px solid #e0e0e0',
  },
  trHover: {
    cursor: 'pointer',
  },
};

function DataTable({ columns, data, onRowClick }) {
  if (!data || data.length === 0) {
    return <p>No data available.</p>;
  }

  return (
    <div style={styles.container}>
      <table style={styles.table}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key} style={styles.th}>
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr
              key={idx}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              style={onRowClick ? styles.trHover : undefined}
              onMouseEnter={(e) => {
                if (onRowClick) e.currentTarget.style.backgroundColor = '#f0f4f8';
              }}
              onMouseLeave={(e) => {
                if (onRowClick) e.currentTarget.style.backgroundColor = '';
              }}
            >
              {columns.map((col) => (
                <td key={col.key} style={styles.td}>
                  {row[col.key] ?? '—'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable;
