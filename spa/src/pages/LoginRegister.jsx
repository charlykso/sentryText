import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Mail, Lock, User, RefreshCw, AlertCircle, ArrowRight, Sun, Moon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LoginRegister() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [gender, setGender] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();
  const { user, loading, login, register, theme, toggleTheme } = useAuth();

  useEffect(() => {
    // Redirect if already authenticated
    if (!loading && user) {
      navigate(user.role === 'admin' ? '/admin' : '/feed');
    }
  }, [user, loading, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    setSuccess('');

    try {
      if (isLogin) {
        await login(email, password);
        navigate('/feed');
      } else {
        if (!username.trim()) throw new Error('Username is required.');
        await register(username.trim(), email, password, gender || null);
        setSuccess('Registration successful! Logging in...');
        setTimeout(() => navigate('/feed'), 1500);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'An error occurred. Please try again.');
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

      {/* Background radial glow */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-brand-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-96 h-96 bg-indigo-600/10 rounded-full blur-[120px] pointer-events-none" />
      
      <div className="w-full max-w-md z-10">
        {/* Logo and Headings */}
        <div className="flex flex-col items-center mb-8 text-center">
          <div className="w-16 h-16 bg-brand-600/10 border border-brand-500/20 rounded-2xl flex items-center justify-center mb-4 shadow-xl shadow-black/20">
            <Shield className="w-8 h-8 text-brand-500" />
          </div>
          <h1 className="font-outfit font-extrabold text-4xl tracking-tight text-dark-100 mb-2">SentryText</h1>
          <p className="text-dark-400 text-sm max-w-xs">Proactive cyberbullying screening for safe online conversations</p>
        </div>

        {/* Authentication Card */}
        <div className="glass-panel rounded-3xl p-8 relative overflow-hidden">
          {/* Top aesthetic light bar */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-brand-500/40 to-transparent" />
          
          <h2 className="text-2xl font-bold font-outfit text-dark-100 mb-6 text-center">
            {isLogin ? 'Sign In to Account' : 'Create New Account'}
          </h2>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4 mb-6 flex items-start gap-3 text-red-400 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="bg-green-500/10 border border-green-500/20 rounded-2xl p-4 mb-6 flex items-center gap-3 text-green-400 text-sm">
              <RefreshCw className="w-5 h-5 animate-spin shrink-0" />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div className="flex flex-col">
                <label className="text-xs font-semibold text-dark-400 mb-1.5 uppercase tracking-wider">Username</label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                  <input
                    type="text"
                    required
                    placeholder="Enter unique handle"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full glass-input pl-12"
                  />
                </div>
              </div>
            )}

            <div className="flex flex-col">
              <label className="text-xs font-semibold text-dark-400 mb-1.5 uppercase tracking-wider">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                <input
                  type="email"
                  required
                  placeholder="name@example.com"
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
                  placeholder="Min 6 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full glass-input pl-12"
                />
              </div>
            </div>

            {!isLogin && (
              <div className="flex flex-col">
                <label className="text-xs font-semibold text-dark-400 mb-1.5 uppercase tracking-wider">Gender (Optional)</label>
                <select
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                  className="w-full glass-input appearance-none bg-dark-950/60"
                  style={{ 
                    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2372869f'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'/%3E%3C/svg%3E")`, 
                    backgroundPosition: 'right 16px center', 
                    backgroundSize: '16px', 
                    backgroundRepeat: 'no-repeat' 
                  }}
                >
                  <option value="" className="bg-dark-950 text-dark-400">Select Gender</option>
                  <option value="Male" className="bg-dark-900 text-dark-100">Male</option>
                  <option value="Female" className="bg-dark-900 text-dark-100">Female</option>
                  <option value="Other" className="bg-dark-900 text-dark-100">Other</option>
                </select>
              </div>
            )}

            <button type="submit" disabled={submitting} className="w-full btn-primary mt-4 flex items-center justify-center gap-2 cursor-pointer">
              {submitting ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <span>{isLogin ? 'Sign In' : 'Sign Up'}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Toggle Sign In / Sign Up */}
          <div className="mt-6 text-center text-sm">
            <span className="text-dark-400">
              {isLogin ? "Don't have an account? " : 'Already have an account? '}
            </span>
            <button
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
                setSuccess('');
              }}
              className="text-brand-400 hover:text-brand-300 font-semibold transition-colors duration-150 cursor-pointer"
            >
              {isLogin ? 'Create Account' : 'Log In'}
            </button>
          </div>
        </div>

        {/* Administrator entry gate */}
        <div className="mt-8 text-center text-sm">
          <Link to="/admin-login" className="text-dark-500 hover:text-brand-400 transition-colors duration-200">
            Access System Administrator Panel →
          </Link>
        </div>
      </div>
    </div>
  );
}
