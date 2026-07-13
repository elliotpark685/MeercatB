import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import AdminLayout from './components/AdminLayoutV2';
import HomeSearch from './pages/HomeSearch';
import Dashboard from './pages/Dashboard';
import LawSearch from './pages/LawSearch';
import DocumentGenerate from './pages/DocumentGenerate';
import SafetyStandardSearch from './pages/SafetyStandardSearch';
import KoshaGuide from './pages/KoshaGuide';
import Login from './pages/Login';
import Register from './pages/Register';
import Spinner from './components/Spinner';
import About from './pages/About';
import Privacy from './pages/Privacy';
import Terms from './pages/Terms';
import Disclaimer from './pages/Disclaimer';
import Contact from './pages/Contact';
import LandingPage from './pages/LandingPage';
import Pricing from './pages/Pricing';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#121212]">
        <Spinner text="세션 확인 중..." />
      </div>
    );
  }
  const redirect = `${location.pathname}${location.search}`;
  return isAuthenticated ? <>{children}</> : <Navigate to={`/login?redirect=${encodeURIComponent(redirect)}`} replace />;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return null;
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <>{children}</>;
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, role } = useAuth();
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#121212]">
        <Spinner text="권한 확인 중..." />
      </div>
    );
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return role === 'admin' ? <>{children}</> : <Navigate to="/" replace />;
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/about" element={<About />} />
            <Route path="/privacy" element={<Privacy locale="en" />} />
            <Route path="/ko/privacy" element={<Privacy locale="ko" />} />
            <Route path="/terms" element={<Terms locale="en" />} />
            <Route path="/ko/terms" element={<Terms locale="ko" />} />
            <Route path="/disclaimer" element={<Disclaimer locale="en" />} />
            <Route path="/ko/disclaimer" element={<Disclaimer locale="ko" />} />
            <Route path="/contact" element={<Contact />} />
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              }
            />
            <Route
              path="/register"
              element={
                <PublicRoute>
                  <Register />
                </PublicRoute>
              }
            />
            <Route
              path="/signup"
              element={
                <PublicRoute>
                  <Register />
                </PublicRoute>
              }
            />
            <Route
              element={
                <ProtectedRoute>
                  <AdminLayout />
                </ProtectedRoute>
              }
            >
              <Route path="dashboard" element={<HomeSearch />} />
              <Route path="admin" element={<AdminRoute><Dashboard /></AdminRoute>} />
              <Route path="laws" element={<LawSearch />} />
              <Route path="safety-standards" element={<SafetyStandardSearch />} />
              <Route path="kosha-guide" element={<KoshaGuide />} />
              <Route path="documents" element={<DocumentGenerate />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ToastProvider>
  );
}
