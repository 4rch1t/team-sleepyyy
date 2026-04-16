import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { setupInterceptors } from './api/client';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import HistoryPage from './pages/HistoryPage';

function ProtectedRoute({ children }) {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

function Navbar() {
  const { token, logout } = useAuth();
  
  return (
    <nav className="w-full border-b border-neutral-800 py-4 px-6 flex justify-between items-center bg-black">
      <div className="text-2xl font-display text-accent tracking-widest font-black">
        VERIFAI
      </div>
      {token && (
        <div className="flex gap-8 font-display uppercase tracking-wider text-sm">
          <Link to="/" className="text-white hover:text-accent transition-colors">Dashboard</Link>
          <Link to="/history" className="text-white hover:text-accent transition-colors">History</Link>
        </div>
      )}
      <div>
        {token ? (
          <button onClick={logout} className="btn-secondary text-sm">Logout</button>
        ) : (
          <Link to="/login" className="btn-primary text-sm inline-block">Login</Link>
        )}
      </div>
    </nav>
  );
}

function App() {
  const { token, logout } = useAuth();

  useEffect(() => {
    setupInterceptors(token, logout);
  }, [token, logout]);

  return (
    <Router>
      <div className="min-h-screen flex flex-col w-full">
        <Navbar />
        <main className="flex-1 w-full p-6">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
            <Route path="/history" element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
