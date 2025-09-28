import { Suspense, lazy } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';

const HomePage = lazy(() => import('./pages/HomePage'));
const LocationPage = lazy(() => import('./pages/LocationPage'));

export default function App() {
  return (
    <Layout>
      <Suspense fallback={<div className="page-loader">Loading…</div>}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/location/:placeId" element={<LocationPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </Layout>
  );
}
