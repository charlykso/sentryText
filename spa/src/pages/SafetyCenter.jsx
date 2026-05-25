import React, { useState, useEffect } from 'react';
import { Info, ShieldAlert, CheckCircle, HelpCircle, Heart, AlertTriangle, RefreshCw } from 'lucide-react';
import { feedService } from '../services/api';

export default function SafetyCenter() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const data = await feedService.getSafetyHistory();
      setHistory(data);
    } catch (err) {
      console.error('Error fetching safety history:', err);
    } finally {
      setLoading(false);
    }
  };

  const guidelines = [
    {
      title: 'Digital Respect & Kindness',
      desc: 'Avoid personal attacks, targeted insults, and abusive slang. Keep online interactions civil and positive.',
      icon: <Heart className="w-5 h-5 text-red-400" />
    },
    {
      title: 'Nigerian Slang Guardrails',
      desc: 'Avoid using Pidgin curses (e.g., "thunder fire you") or abusive slang (e.g., "mumu", "olodo", "ashawo", "ewu") that are flagged as toxic by the engine.',
      icon: <ShieldAlert className="w-5 h-5 text-brand-500" />
    },
    {
      title: 'Proactive Edits',
      desc: 'If a post, comment, or chat message is blocked by SentryText, simply edit the text to remove aggressive terms before attempting to submit again.',
      icon: <CheckCircle className="w-5 h-5 text-green-400" />
    },
    {
      title: 'External Message Audits',
      desc: 'Utilize the External Auditor scratchpad to check WhatsApp, Facebook, or Instagram messages before sharing them with your social circles.',
      icon: <HelpCircle className="w-5 h-5 text-indigo-400" />
    }
  ];

  const totalViolations = history.filter(item => item.ModerationStatus === 'Blocked').length;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col items-center text-center">
        <div className="w-12 h-12 bg-brand-500/10 border border-brand-500/20 rounded-2xl flex items-center justify-center mb-3">
          <Info className="w-6 h-6 text-brand-500" />
        </div>
        <h2 className="font-outfit font-extrabold text-3xl text-dark-100">Personal Safety Center</h2>
        <p className="text-dark-400 text-sm max-w-md mt-1.5">Review digital safety guidelines and track your personal account interaction logs.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Guidelines */}
        <div className="space-y-4 lg:col-span-1">
          <h3 className="text-xs uppercase font-bold text-dark-400 tracking-wider">Platform Safety Guidelines</h3>
          <div className="space-y-3">
            {guidelines.map((g, idx) => (
              <div key={idx} className="glass-panel p-5 rounded-2xl flex gap-4 border border-dark-800">
                <div className="w-10 h-10 rounded-xl bg-dark-950 flex items-center justify-center shrink-0 border border-dark-800">
                  {g.icon}
                </div>
                <div>
                  <h4 className="font-outfit font-bold text-sm text-dark-100">{g.title}</h4>
                  <p className="text-xs text-dark-400 mt-1 leading-relaxed">{g.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* User Flagged Logs */}
        <div className="space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs uppercase font-bold text-dark-400 tracking-wider">Your Interaction Logs</h3>
            <span className="text-xs px-2.5 py-1 rounded-full font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
              Total Interceptions: {totalViolations}
            </span>
          </div>

          <div className="glass-panel rounded-3xl p-6 border border-dark-800 space-y-4 min-h-[40vh]">
            {loading ? (
              <div className="h-full flex items-center justify-center py-20 text-sm text-dark-500 gap-2">
                <RefreshCw className="w-5 h-5 animate-spin text-brand-500" /> Fetching personal safety records...
              </div>
            ) : history.length === 0 ? (
              <div className="flex flex-col items-center justify-center text-center text-dark-500 py-16">
                <div className="w-12 h-12 rounded-2xl bg-green-500/10 border border-green-500/20 flex items-center justify-center mb-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                </div>
                <p className="font-semibold text-dark-100">Your Feed is Clean!</p>
                <p className="text-xs mt-1 max-w-xs">You have no active content flags or blocked submissions on SentryText. Keep up the good work!</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[50vh] overflow-y-auto pr-1">
                {history.map((log) => {
                  const isBlocked = log.ModerationStatus === 'Blocked';
                  return (
                    <div 
                      key={log.Id} 
                      className={`p-4 rounded-2xl border ${isBlocked ? 'bg-red-500/5 border-red-500/10' : 'bg-green-500/5 border-green-500/10'} flex items-start justify-between gap-4`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold capitalize ${isBlocked ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'}`}>
                            {log.ContentType}
                          </span>
                          <span className="text-[10px] text-dark-500">{new Date(log.Timestamp).toLocaleString()}</span>
                        </div>
                        <p className={`text-sm leading-relaxed ${isBlocked ? 'text-red-300/80 italic' : 'text-dark-200'}`}>
                          "{log.RawText}"
                        </p>
                      </div>
                      
                      <div className="text-right shrink-0">
                        <span className={`text-xs font-bold font-outfit block ${isBlocked ? 'text-red-500' : 'text-green-500'}`}>
                          {log.ModerationStatus}
                        </span>
                        <span className="text-[10px] text-dark-500 block mt-0.5">
                          Conf: {log.ConfidenceScore}%
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
