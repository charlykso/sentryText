import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { Shield, MessageSquare, Newspaper, Info, Activity, LogOut, Sun, Moon } from 'lucide-react';
import LoginRegister from './pages/LoginRegister';
import AdminLogin from './pages/AdminLogin';
import Feed from './pages/Feed';
import Chat from './pages/Chat';
import SafetyCenter from './pages/SafetyCenter';
import Auditor from './pages/Auditor';
import AdminDashboard from './pages/AdminDashboard';
import { AuthProvider, useAuth } from './context/AuthContext';

const ProtectedRoute = ({ children, allowedRole = 'user' }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-950">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-brand-600/10 border border-brand-500/20 flex items-center justify-center shadow-lg shadow-black/20 animate-spin">
            <Shield className="w-6 h-6 text-brand-500" />
          </div>
          <span className="text-sm text-dark-400 font-medium">Verifying secure session...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to={allowedRole === 'admin' ? '/admin-login' : '/'} replace />;
  }

  if (user.role !== allowedRole) {
    return <Navigate to={user.role === 'admin' ? '/admin' : '/feed'} replace />;
  }

  return children;
};

const NavBar = () => {
  const location = useLocation();
  const { user, logout, theme, toggleTheme } = useAuth();
  const role = user?.role;
  const userName = user?.name || 'User';

  const isActive = (path) => location.pathname === path;

  const handleLogout = () => {
    logout();
  };

  const themeToggleButton = (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-xl text-dark-300 hover:text-dark-100 hover:bg-dark-900/60 transition-colors duration-200 flex items-center justify-center shrink-0 cursor-pointer"
      title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
    >
      {theme === 'dark' ? <Sun className="w-5 h-5 text-yellow-500" /> : <Moon className="w-5 h-5 text-indigo-500" />}
    </button>
  );

  if (role === 'admin') {
    return (
      <nav className="glass-panel border-b border-dark-800/80 px-6 py-4 sticky top-0 z-40 flex items-center justify-between">
        <Link to="/admin" className="flex items-center gap-2 hover:opacity-90 transition-opacity duration-200">
          <Shield className="w-6 h-6 text-brand-500" />
          <span className="font-outfit font-extrabold text-xl tracking-tight text-gradient">SentryText Admin</span>
        </Link>
        <div className="flex items-center gap-6">
          <span className="text-sm text-dark-400 font-medium">
            Welcome, <strong className="text-brand-400">{userName}</strong> (Administrator)
          </span>
          {themeToggleButton}
          <button onClick={handleLogout} className="flex items-center gap-1.5 text-sm text-red-400 hover:text-red-300 font-semibold transition-colors duration-200 cursor-pointer">
            <LogOut className="w-4 h-4" /> Logout
          </button>
        </div>
      </nav>
    );
  }

  return (
    <nav className="glass-panel border-b border-dark-800/80 px-6 py-4 sticky top-0 z-40 flex items-center justify-between">
      <Link to="/feed" className="flex items-center gap-2 hover:opacity-90 transition-opacity duration-200">
        <Shield className="w-6 h-6 text-brand-500" />
        <span className="font-outfit font-extrabold text-xl tracking-tight text-gradient font-sans">SentryText</span>
      </Link>
      
      <div className="flex items-center gap-2 md:gap-3">
        <Link to="/feed" className={`flex items-center gap-1.5 px-3 md:px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${isActive('/feed') ? 'bg-brand-600/10 text-brand-400 border border-brand-500/20' : 'text-dark-300 hover:text-dark-100 hover:bg-dark-900/60'}`}>
          <Newspaper className="w-4 h-4" /> <span className="hidden sm:inline">Social Feed</span>
        </Link>
        <Link to="/chat" className={`flex items-center gap-1.5 px-3 md:px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${isActive('/chat') ? 'bg-brand-600/10 text-brand-400 border border-brand-500/20' : 'text-dark-300 hover:text-dark-100 hover:bg-dark-900/60'}`}>
          <MessageSquare className="w-4 h-4" /> <span className="hidden sm:inline">Private Chat</span>
        </Link>
        <Link to="/auditor" className={`flex items-center gap-1.5 px-3 md:px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${isActive('/auditor') ? 'bg-brand-600/10 text-brand-400 border border-brand-500/20' : 'text-dark-300 hover:text-dark-100 hover:bg-dark-900/60'}`}>
          <Activity className="w-4 h-4" /> <span className="hidden sm:inline">Text Auditor</span>
        </Link>
        <Link to="/safety" className={`flex items-center gap-1.5 px-3 md:px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${isActive('/safety') ? 'bg-brand-600/10 text-brand-400 border border-brand-500/20' : 'text-dark-300 hover:text-dark-100 hover:bg-dark-900/60'}`}>
          <Info className="w-4 h-4" /> <span className="hidden sm:inline">Safety Center</span>
        </Link>
      </div>

      <div className="flex items-center gap-4">
        <span className="hidden md:inline text-sm text-dark-400 font-medium">Hello, <strong className="text-dark-100">{userName}</strong></span>
        {themeToggleButton}
        <button onClick={handleLogout} className="flex items-center gap-1.5 text-sm text-dark-300 hover:text-red-400 font-semibold transition-colors duration-200 cursor-pointer">
          <LogOut className="w-4 h-4" /> <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </nav>
  );
};

const MainLayout = ({ children }) => {
  return (
    <div className="flex flex-col min-h-screen bg-dark-950">
      <NavBar />
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 lg:p-8 animate-fadeIn">
        {children}
      </main>
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public auth pages */}
          <Route path="/" element={<LoginRegister />} />
          <Route path="/admin-login" element={<AdminLogin />} />

          {/* Protected user pages */}
          <Route path="/feed" element={<ProtectedRoute><MainLayout><Feed /></MainLayout></ProtectedRoute>} />
          <Route path="/chat" element={<ProtectedRoute><MainLayout><Chat /></MainLayout></ProtectedRoute>} />
          <Route path="/safety" element={<ProtectedRoute><MainLayout><SafetyCenter /></MainLayout></ProtectedRoute>} />
          <Route path="/auditor" element={<ProtectedRoute><MainLayout><Auditor /></MainLayout></ProtectedRoute>} />

          {/* Protected admin pages */}
          <Route path="/admin" element={<ProtectedRoute allowedRole="admin"><MainLayout><AdminDashboard /></MainLayout></ProtectedRoute>} />

          {/* Fallback redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
