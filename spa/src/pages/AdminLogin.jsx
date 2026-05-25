import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Mail, Lock, RefreshCw, AlertCircle, ArrowRight, Sun, Moon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function AdminLogin() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { user, loading, adminLogin, theme, toggleTheme } = useAuth();

  useEffect(() => {
    if (!loading && user) {
      navigate(user.role === 'admin' ? '/admin' : '/feed');
    }
  }, [user, loading, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      await adminLogin(email, password);
      navigate('/admin');
    } catch (err) {
      setError(err.response?.data?.detail || 'Incorrect admin email or password.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-950">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-brand-600/10 border border-brand-500/20 flex items-center justify-center shadow-lg shadow-black/20 animate-spin">
            <Shield className="w-6 h-6 text-brand-500" />
          </div>
          <span className="text-sm text-dark-400 font-medium">Loading SentryText...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-dark-950 px-4 overflow-hidden">
      {/* Theme Toggle Button */}
      <button 
        onClick={toggleTheme} 
        className="absolute top-6 right-6 p-3 rounded-2xl bg-dark-900/60 border border-dark-800/80 text-dark-300 hover:text-dark-100 hover:bg-dark-900 transition-all duration-200 shadow-lg cursor-pointer"
        title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
      >
        {theme === 'dark' ? <Sun className="w-5 h-5 text-yellow-500" /> : <Moon className="w-5 h-5 text-indigo-500" />}
      </button>

      {/* Background gradients */}
      <div className="absolute top-1/4 right-1/4 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-red-600/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/4 translate-x-1/2 translate-y-1/2 w-96 h-96 bg-brand-600/10 rounded-full blur-[120px] pointer-events-none" />
      
      <div className="w-full max-w-md z-10">
        {/* Logo and Headings */}
        <div className="flex flex-col items-center mb-8 text-center">
          <div className="w-16 h-16 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center justify-center mb-4 shadow-xl shadow-black/20">
            <Shield className="w-8 h-8 text-red-500" />
          </div>
          <h1 className="font-outfit font-extrabold text-4xl tracking-tight text-dark-100 mb-2">SentryText Admin</h1>
          <p className="text-dark-400 text-sm max-w-xs">Privileged access portal for moderating platform activities</p>
        </div>

        {/* Admin Login Card */}
        <div className="glass-panel rounded-3xl p-8 relative overflow-hidden">
          {/* Top aesthetic red bar for admin focus */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-red-500/40 to-transparent" />
          
          <h2 className="text-2xl font-bold font-outfit text-dark-100 mb-6 text-center">
            Privileged Sign In
          </h2>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4 mb-6 flex items-start gap-3 text-red-400 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex flex-col">
              <label className="text-xs font-semibold text-dark-400 mb-1.5 uppercase tracking-wider">Admin Email</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                <input
                  type="email"
                  required
                  placeholder="admin@sentrytext.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full glass-input pl-12"
                />
              </div>
            </div>

            <div className="flex flex-col">
              <label className="text-xs font-semibold text-dark-400 mb-1.5 uppercase tracking-wider">Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                <input
                  type="password"
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full glass-input pl-12"
                />
              </div>
            </div>

            <button type="submit" disabled={submitting} className="w-full bg-red-600 hover:bg-red-500 text-white rounded-xl px-5 py-3 font-semibold shadow-lg shadow-red-600/20 hover:shadow-red-500/30 active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:pointer-events-none mt-4 flex items-center justify-center gap-2 cursor-pointer">
              {submitting ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <span>Sign In as Admin</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Back link */}
          <div className="mt-6 text-center text-sm">
            <Link to="/" className="text-dark-400 hover:text-brand-400 transition-colors duration-150">
              ← Return to Standard User Log In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
