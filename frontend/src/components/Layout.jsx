import { Link, useLocation } from 'react-router-dom';

const styles = {
  header: {
    backgroundColor: '#003366',
    color: '#ffffff',
    padding: '0 24px',
    display: 'flex',
    alignItems: 'center',
    height: 56,
    gap: 32,
  },
  title: {
    fontSize: 20,
    fontWeight: 700,
    letterSpacing: 0.5,
  },
  nav: {
    display: 'flex',
    gap: 16,
  },
  navLink: {
    color: '#ccd6e0',
    fontSize: 14,
    textDecoration: 'none',
  },
  navLinkActive: {
    color: '#ffffff',
    fontSize: 14,
    textDecoration: 'none',
    fontWeight: 600,
  },
  main: {
    maxWidth: 1200,
    margin: '24px auto',
    padding: '0 24px',
  },
};

function Layout({ children }) {
  const location = useLocation();
  const isHome = location.pathname === '/';

  return (
    <div>
      <header style={styles.header}>
        <Link to="/" style={{ ...styles.navLink, ...styles.title, color: '#fff' }}>
          FRED Data Explorer
        </Link>
        <nav style={styles.nav}>
          <Link
            to="/"
            style={isHome ? styles.navLinkActive : styles.navLink}
          >
            Search
          </Link>
        </nav>
      </header>
      <main style={styles.main}>{children}</main>
    </div>
  );
}

export default Layout;
