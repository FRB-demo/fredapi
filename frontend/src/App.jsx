import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import SearchPage from './pages/SearchPage';
import SeriesDetailPage from './pages/SeriesDetailPage';
import RevisionHistoryPage from './pages/RevisionHistoryPage';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/series/:id" element={<SeriesDetailPage />} />
        <Route path="/series/:id/revisions" element={<RevisionHistoryPage />} />
      </Routes>
    </Layout>
  );
}

export default App;
