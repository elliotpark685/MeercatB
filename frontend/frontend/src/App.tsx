import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import AdminLayout from './components/AdminLayout';
import Dashboard from './pages/Dashboard';
import LawSearch from './pages/LawSearch';
import DocumentGenerate from './pages/DocumentGenerate';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AdminLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="laws" element={<LawSearch />} />
            <Route path="documents" element={<DocumentGenerate />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
