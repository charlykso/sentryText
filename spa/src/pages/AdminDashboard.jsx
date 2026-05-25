import React, { useState, useEffect } from 'react';
import { Shield, Users, Newspaper, AlertTriangle, ShieldCheck, Search, Filter, Cpu, RefreshCw, Calendar, Trash2, ShieldAlert } from 'lucide-react';
import { adminService } from '../services/api';

export default function AdminDashboard() {
  const [telemetry, setTelemetry] = useState(null);
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All'); // All, Approved, Blocked
  const [typeFilter, setTypeFilter] = useState('All'); // All, post, comment, message
  
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // User Directory state
  const [activeTab, setActiveTab] = useState('telemetry'); // telemetry, users
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [searchUserQuery, setSearchUserQuery] = useState('');

  // Deletion Confirmation Modal state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);
  const [deletingUser, setDeletingUser] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [logs, searchQuery, statusFilter, typeFilter]);

  useEffect(() => {
    if (activeTab === 'users') {
      fetchUsers();
    }
  }, [activeTab]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const telData = await adminService.getTelemetry();
      const logsData = await adminService.getLogs();
      setTelemetry(telData);
      setLogs(logsData);
    } catch (err) {
      console.error('Error fetching admin dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    setLoadingUsers(true);
    try {
      const data = await adminService.getUsers();
      setUsers(data);
    } catch (err) {
      console.error('Error fetching user directory:', err);
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const telData = await adminService.getTelemetry();
      setTelemetry(telData);
      if (activeTab === 'telemetry') {
        const logsData = await adminService.getLogs();
        setLogs(logsData);
      } else if (activeTab === 'users') {
        await fetchUsers();
      }
    } catch (err) {
      console.error('Error refreshing dashboard:', err);
    } finally {
      setRefreshing(false);
    }
  };

  const applyFilters = () => {
    let result = [...logs];

    // Search filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(log => log.RawText.toLowerCase().includes(q));
    }

    // Status filter
    if (statusFilter !== 'All') {
      result = result.filter(log => log.ModerationStatus === statusFilter);
    }

    // Content type filter
    if (typeFilter !== 'All') {
      result = result.filter(log => log.ContentType === typeFilter);
    }

    setFilteredLogs(result);
  };

  const handleDeleteUser = async () => {
    if (!userToDelete) return;
    setDeletingUser(true);
    setDeleteError('');
    try {
      await adminService.deleteUser(userToDelete.Id);
      // Refresh telemetry
      const telData = await adminService.getTelemetry();
      setTelemetry(telData);
      // Refresh users
      await fetchUsers();
      setShowDeleteModal(false);
      setUserToDelete(null);
    } catch (err) {
      setDeleteError(err.response?.data?.detail || 'Failed to delete user.');
    } finally {
      setDeletingUser(false);
    }
  };

  // Filtered users list
  const filteredUsers = users.filter(u => {
    const q = searchUserQuery.toLowerCase().trim();
    if (!q) return true;
    return u.Username.toLowerCase().includes(q) || u.Email.toLowerCase().includes(q);
  });

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center justify-center">
            <Shield className="w-6 h-6 text-red-500" />
          </div>
          <div>
            <h2 className="font-outfit font-extrabold text-3xl text-dark-100">Operations Dashboard</h2>
            <p className="text-dark-400 text-sm mt-0.5">Live monitoring of system operations, prediction metrics, and content audit logs.</p>
          </div>
        </div>
        
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="btn-secondary text-sm flex items-center justify-center gap-2 self-start sm:self-auto"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin text-brand-500' : ''}`} />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-dark-850 gap-2">
        <button
          onClick={() => setActiveTab('telemetry')}
          className={`flex items-center gap-2 px-6 py-3 border-b-2 font-semibold transition-all duration-200 text-sm ${activeTab === 'telemetry' ? 'border-brand-500 text-brand-400' : 'border-transparent text-dark-400 hover:text-dark-100'}`}
        >
          <Cpu className="w-4 h-4" /> Telemetry & Audit Logs
        </button>
        <button
          onClick={() => setActiveTab('users')}
          className={`flex items-center gap-2 px-6 py-3 border-b-2 font-semibold transition-all duration-200 text-sm ${activeTab === 'users' ? 'border-brand-500 text-brand-400' : 'border-transparent text-dark-400 hover:text-dark-100'}`}
        >
          <Users className="w-4 h-4" /> User Directory
        </button>
      </div>

      {activeTab === 'telemetry' ? (
        <>
          {/* Telemetry Counter Grid */}
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
              {[1, 2, 3, 4].map(idx => (
                <div key={idx} className="bg-dark-900/50 border border-dark-850 rounded-3xl h-32" />
              ))}
            </div>
          ) : telemetry ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Card 1: Users */}
              <div className="glass-panel p-6 rounded-3xl border border-dark-800 flex items-center justify-between">
                <div className="space-y-1">
                  <span className="text-xs font-semibold text-dark-500 uppercase tracking-wider">Registered Users</span>
                  <strong className="text-3xl font-outfit font-extrabold text-dark-100 block">{telemetry.total_users}</strong>
                </div>
                <div className="w-12 h-12 bg-brand-500/10 rounded-2xl flex items-center justify-center border border-brand-500/10">
                  <Users className="w-5 h-5 text-brand-400" />
                </div>
              </div>

              {/* Card 2: Total Posts */}
              <div className="glass-panel p-6 rounded-3xl border border-dark-800 flex items-center justify-between">
                <div className="space-y-1">
                  <span className="text-xs font-semibold text-dark-500 uppercase tracking-wider">Global Posts</span>
                  <strong className="text-3xl font-outfit font-extrabold text-dark-100 block">{telemetry.total_posts}</strong>
                </div>
                <div className="w-12 h-12 bg-indigo-500/10 rounded-2xl flex items-center justify-center border border-indigo-500/10">
                  <Newspaper className="w-5 h-5 text-indigo-400" />
                </div>
              </div>

              {/* Card 3: Approved Submissions */}
              <div className="glass-panel p-6 rounded-3xl border border-dark-800 flex items-center justify-between">
                <div className="space-y-1">
                  <span className="text-xs font-semibold text-dark-500 uppercase tracking-wider">Approved Content</span>
                  <strong className="text-3xl font-outfit font-extrabold text-green-400 block">{telemetry.total_approved}</strong>
                </div>
                <div className="w-12 h-12 bg-green-500/10 rounded-2xl flex items-center justify-center border border-green-500/10">
                  <ShieldCheck className="w-5 h-5 text-green-400" />
                </div>
              </div>

              {/* Card 4: Blocked Violations */}
              <div className="glass-panel p-6 rounded-3xl border border-red-500/10 flex items-center justify-between">
                <div className="space-y-1">
                  <span className="text-xs font-semibold text-dark-500 uppercase tracking-wider">Blocked Violations</span>
                  <strong className="text-3xl font-outfit font-extrabold text-red-500 block">{telemetry.total_violations}</strong>
                </div>
                <div className="w-12 h-12 bg-red-500/10 rounded-2xl flex items-center justify-center border border-red-500/10">
                  <AlertTriangle className="w-5 h-5 text-red-450" />
                </div>
              </div>
            </div>
          ) : null}

          {/* Audit Log Controls (Search & Filters) */}
          <div className="glass-panel rounded-3xl p-6 border border-dark-800 space-y-4">
            <h3 className="font-outfit font-bold text-dark-100 text-lg">Granular Moderation Review Grid</h3>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* Search bar */}
              <div className="relative">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                <input
                  type="text"
                  placeholder="Search raw text content..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full glass-input py-2 pl-10 pr-4 text-sm rounded-xl"
                />
              </div>

              {/* Status Filter */}
              <div className="relative flex items-center">
                <Filter className="absolute left-3.5 w-4 h-4 text-dark-500" />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full glass-input py-2 pl-10 pr-4 text-sm rounded-xl appearance-none bg-dark-950/60"
                >
                  <option value="All">All Verdicts</option>
                  <option value="Approved">Approved Only</option>
                  <option value="Blocked">Blocked Only</option>
                </select>
              </div>

              {/* Type Filter */}
              <div className="relative flex items-center">
                <Cpu className="absolute left-3.5 w-4 h-4 text-dark-500" />
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="w-full glass-input py-2 pl-10 pr-4 text-sm rounded-xl appearance-none bg-dark-950/60"
                >
                  <option value="All">All Content Types</option>
                  <option value="post">Posts Only</option>
                  <option value="comment">Comments Only</option>
                  <option value="message">Direct Messages Only</option>
                </select>
              </div>
              
              {/* Active Log Counter */}
              <div className="bg-dark-950/40 rounded-xl px-4 py-2 border border-dark-850 flex items-center justify-between text-xs text-dark-400">
                <span>Filtered Logs:</span>
                <strong className="text-dark-100 font-semibold font-outfit text-sm">{filteredLogs.length} / {logs.length}</strong>
              </div>
            </div>

            {/* Audit Log Table Grid */}
            <div className="overflow-x-auto rounded-2xl border border-dark-850 bg-dark-950/20">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-dark-900/60 border-b border-dark-850 text-xs font-semibold text-dark-400 uppercase tracking-wider">
                    <th className="p-4">Type</th>
                    <th className="p-4">Raw Text Snippet</th>
                    <th className="p-4">ML Label</th>
                    <th className="p-4">Confidence</th>
                    <th className="p-4">Verdict Action</th>
                    <th className="p-4"><span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> Date & Time</span></th>
                  </tr>
                </thead>
                
                <tbody className="divide-y divide-dark-850 text-sm text-dark-200">
                  {loading ? (
                    <tr>
                      <td colSpan="6" className="p-8 text-center text-dark-500">
                        <RefreshCw className="w-6 h-6 animate-spin mx-auto text-brand-500 mb-2" /> Loading operations telemetry logs...
                      </td>
                    </tr>
                  ) : filteredLogs.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="p-8 text-center text-dark-550">
                        No moderation records match the active search/filters.
                      </td>
                    </tr>
                  ) : (
                    filteredLogs.map((log) => {
                      const isBlocked = log.ModerationStatus === 'Blocked';
                      return (
                        <tr key={log.Id} className="hover:bg-dark-900/25 transition-colors">
                          <td className="p-4">
                            <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${log.ContentType === 'post' ? 'bg-indigo-500/10 text-indigo-400' : log.ContentType === 'comment' ? 'bg-purple-500/10 text-purple-400' : 'bg-brand-500/10 text-brand-400'}`}>
                              {log.ContentType}
                            </span>
                          </td>
                          <td className="p-4 max-w-xs sm:max-w-md truncate" title={log.RawText}>
                            <span className={isBlocked ? 'text-red-300/80 italic font-mono text-xs' : ''}>
                              {log.RawText}
                            </span>
                          </td>
                          <td className="p-4">
                            <span className={`font-semibold ${log.Classification === 'Harmful' ? 'text-red-400' : 'text-green-400'}`}>
                              {log.Classification}
                            </span>
                          </td>
                          <td className="p-4 font-mono text-xs font-semibold">{log.ConfidenceScore}%</td>
                          <td className="p-4">
                            <span className={`text-xs font-bold ${isBlocked ? 'text-red-500' : 'text-green-500'}`}>
                              {log.ModerationStatus}
                            </span>
                          </td>
                          <td className="p-4 text-xs text-dark-400 font-medium">
                            {new Date(log.Timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        /* USER DIRECTORY TAB VIEW */
        <div className="glass-panel rounded-3xl p-6 border border-dark-800 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <h3 className="font-outfit font-bold text-dark-100 text-lg">System User Management</h3>
            
            {/* Search user bar */}
            <div className="relative w-full sm:w-72">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
              <input
                type="text"
                placeholder="Search handle or email..."
                value={searchUserQuery}
                onChange={(e) => setSearchUserQuery(e.target.value)}
                className="w-full glass-input py-2 pl-10 pr-4 text-sm rounded-xl"
              />
            </div>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-dark-850 bg-dark-950/20">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-dark-900/60 border-b border-dark-850 text-xs font-semibold text-dark-400 uppercase tracking-wider">
                  <th className="p-4">User</th>
                  <th className="p-4">Email</th>
                  <th className="p-4 text-center">Gender</th>
                  <th className="p-4 text-center">Posts</th>
                  <th className="p-4 text-center">Comments</th>
                  <th className="p-4 text-center">Violations</th>
                  <th className="p-4"><span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> Registered Date</span></th>
                  <th className="p-4 text-center">Actions</th>
                </tr>
              </thead>
              
              <tbody className="divide-y divide-dark-850 text-sm text-dark-200">
                {loadingUsers ? (
                  <tr>
                    <td colSpan="8" className="p-8 text-center text-dark-500">
                      <RefreshCw className="w-6 h-6 animate-spin mx-auto text-brand-500 mb-2" /> Loading user registry records...
                    </td>
                  </tr>
                ) : filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="p-8 text-center text-dark-550">
                      No registered user accounts match the search term.
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map((u) => {
                    const hasViolations = u.ViolationCount > 0;
                    return (
                      <tr key={u.Id} className="hover:bg-dark-900/25 transition-colors">
                        <td className="p-4">
                          <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-lg bg-dark-900 border border-dark-800 text-xs font-bold text-dark-300 flex items-center justify-center uppercase">
                              {u.Username.substring(0, 2)}
                            </div>
                            <span className="font-semibold text-dark-100 capitalize">{u.Username}</span>
                          </div>
                        </td>
                        <td className="p-4 text-dark-300 font-mono text-xs">{u.Email}</td>
                        <td className="p-4 text-center text-xs text-dark-400 font-semibold">{u.Gender || 'N/A'}</td>
                        <td className="p-4 text-center font-mono font-semibold">{u.PostCount}</td>
                        <td className="p-4 text-center font-mono font-semibold">{u.CommentCount}</td>
                        <td className="p-4 text-center">
                          <span className={`inline-block font-mono font-bold px-2 py-0.5 rounded-full text-xs ${hasViolations ? 'bg-red-500/10 text-red-500 border border-red-500/20' : 'bg-green-500/10 text-green-500'}`}>
                            {u.ViolationCount}
                          </span>
                        </td>
                        <td className="p-4 text-xs text-dark-400 font-medium">
                          {new Date(u.DateRegistered).toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' })}
                        </td>
                        <td className="p-4 text-center">
                          <button
                            onClick={() => {
                              setUserToDelete(u);
                              setShowDeleteModal(true);
                            }}
                            className="p-1.5 rounded-lg text-dark-400 hover:text-red-400 hover:bg-red-500/10 transition-all duration-200"
                            title={`Purge user '${u.Username}'`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* CONFIRM USER DELETION MODAL */}
      {showDeleteModal && userToDelete && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
          <div className="glass-panel w-full max-w-md rounded-3xl p-6 relative shadow-2xl border-red-500/20">
            <div className="absolute top-0 left-0 right-0 h-[3px] bg-red-500" />
            
            <div className="flex items-start gap-4 mb-4">
              <div className="w-12 h-12 rounded-2xl bg-red-500/10 border border-red-500/25 flex items-center justify-center shrink-0">
                <ShieldAlert className="w-6 h-6 text-red-500" />
              </div>
              <div>
                <h3 className="font-outfit font-extrabold text-xl text-dark-100">Purge User Profile?</h3>
                <p className="text-sm text-dark-400 mt-1">This administrative action is irreversible.</p>
              </div>
            </div>

            <div className="bg-dark-950/80 rounded-2xl p-4 border border-dark-900 mb-6">
              <p className="text-dark-200 text-sm">
                Deleting user <strong className="text-dark-100 capitalize">@{userToDelete.Username}</strong> will purge:
              </p>
              <ul className="list-disc list-inside text-xs text-dark-400 mt-2 space-y-1">
                <li>Account credentials & details</li>
                <li>All posts ({userToDelete.PostCount}) & comments ({userToDelete.CommentCount})</li>
                <li>All private direct messages & logs</li>
              </ul>
            </div>

            {deleteError && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-4 text-xs text-red-400">
                {deleteError}
              </div>
            )}

            <div className="flex justify-end gap-3">
              <button
                disabled={deletingUser}
                onClick={() => {
                  setShowDeleteModal(false);
                  setUserToDelete(null);
                  setDeleteError('');
                }}
                className="btn-secondary text-sm px-4 py-2"
              >
                Cancel
              </button>
              <button
                disabled={deletingUser}
                onClick={handleDeleteUser}
                className="bg-red-650 hover:bg-red-550 text-white rounded-xl px-5 py-2 font-semibold text-sm transition-all duration-200 flex items-center gap-1.5 disabled:opacity-50"
              >
                {deletingUser ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    <span>Purge User Data</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
