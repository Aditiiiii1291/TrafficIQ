import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Layout
import DashboardLayout from './layouts/DashboardLayout';

// Pages
import Dashboard from './pages/Dashboard';
import UploadVideo from './pages/UploadVideo';
import Analytics from './pages/Analytics';
import History from './pages/History';
import Results from './pages/Results';
import NotFound from './pages/NotFound';

// Setup TanStack Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Main Dashboard Layout Route */}
          <Route path="/" element={<DashboardLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="upload" element={<UploadVideo />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="history" element={<History />} />
            <Route path="results" element={<Results />} />
            {/* Catch-all 404 Route inside layout */}
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
