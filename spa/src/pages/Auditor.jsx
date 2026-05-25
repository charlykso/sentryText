import React, { useState } from 'react';
import { Activity, Clipboard, ShieldAlert, CheckCircle, Cpu, AlertTriangle, MessageSquare, RefreshCw } from 'lucide-react';
import { auditorService } from '../services/api';

export default function Auditor() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  // Ready-to-test sample messages (some safe, some toxic with slang)
  const samples = [
    { label: 'Safe English & Pidgin', text: 'Good morning my people! Abeg check this update, the jollof rice recipe is correct and very easy to prepare. Bless up!' },
    { label: 'Toxic Slang Comment', text: 'mtcheew, you are a complete mumu Olodo boy. stop posting about your trash life, thunder fire you and your generation!' },
    { label: 'Standard Cyberbullying', text: 'You are the most pathetic and stupid loser on this platform. Everyone hates you. Go delete your account and disappear.' }
  ];

  const handleAudit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    setLoading(true);
    setResult(null);

    try {
      const data = await auditorService.analyzeText(text);
      setResult(data);
    } catch (err) {
      console.error('Error auditing text:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadSample = (sampleText) => {
    setText(sampleText);
    setResult(null);
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Page Title */}
      <div className="flex flex-col items-center text-center">
        <div className="w-12 h-12 bg-brand-500/10 border border-brand-500/20 rounded-2xl flex items-center justify-center mb-3">
          <Activity className="w-6 h-6 text-brand-500" />
        </div>
        <h2 className="font-outfit font-extrabold text-3xl text-dark-100">External Text Auditor</h2>
        <p className="text-dark-400 text-sm max-w-md mt-1.5">Paste text snippets copied from external platforms (WhatsApp, Facebook, Instagram) to run a pre-sharing toxicity audit.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Quick Test Samples */}
        <div className="space-y-4">
          <h3 className="text-xs uppercase font-bold text-dark-400 tracking-wider">Quick Templates</h3>
          <div className="space-y-2">
            {samples.map((s, idx) => (
              <button
                key={idx}
                onClick={() => loadSample(s.text)}
                className="w-full text-left p-3 rounded-2xl glass-panel glass-panel-hover text-xs border border-dark-800"
              >
                <span className="font-bold text-brand-400 block mb-1">{s.label}</span>
                <p className="text-dark-350 line-clamp-2 italic">"{s.text}"</p>
              </button>
            ))}
          </div>
        </div>

        {/* Right Columns: Large Audit Workspace */}
        <div className="md:col-span-2 space-y-6">
          <div className="glass-panel rounded-3xl p-6 relative">
            <div className="flex items-center gap-2 mb-4">
              <Clipboard className="w-5 h-5 text-brand-500" />
              <h3 className="font-outfit font-bold text-dark-100 text-lg font-sans">Auditing Workspace</h3>
            </div>
            
            <form onSubmit={handleAudit} className="space-y-4">
              <textarea
                required
                rows="5"
                placeholder="Paste text contents from external messaging apps here to evaluate safety..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                className="w-full glass-input resize-none"
                disabled={loading}
              />
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={loading || !text.trim()}
                  className="btn-primary flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Auditing Text...</span>
                    </>
                  ) : (
                    <>
                      <Activity className="w-4 h-4" />
                      <span>Audit Text</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Audit Result Display */}
          {result && (
            <div className={`glass-panel rounded-3xl p-6 border animate-scaleUp ${result.classification === 'Harmful' ? 'border-red-500/20' : 'border-green-500/20'}`}>
              <div className="flex items-start gap-4 mb-6">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${result.classification === 'Harmful' ? 'bg-red-500/10' : 'bg-green-500/10'}`}>
                  {result.classification === 'Harmful' ? (
                    <AlertTriangle className="w-6 h-6 text-red-500" />
                  ) : (
                    <CheckCircle className="w-6 h-6 text-green-500" />
                  )}
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-wider text-dark-500">Audit Safety Verdict</span>
                  <h4 className={`font-outfit font-extrabold text-xl ${result.classification === 'Harmful' ? 'text-red-500' : 'text-green-500'}`}>
                    {result.classification === 'Harmful' ? 'Harmful (Cyberbullying Detected)' : 'Safe (Non-Harmful Content)'}
                  </h4>
                  <p className="text-xs text-dark-400 mt-1">
                    {result.classification === 'Harmful' 
                      ? 'This text contains abusive language, regional Pidgin slangs, or toxic comments and should not be shared.' 
                      : 'This text is clear of detected toxicity and is safe to be sent.'}
                  </p>
                </div>
              </div>

              {/* Stats telemetry */}
              <div className="space-y-4">
                <h5 className="text-xs uppercase font-bold text-dark-400 tracking-wider flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-brand-500" /> Diagnostic Model Breakdown
                </h5>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="bg-dark-950/40 border border-dark-850 rounded-2xl p-4 text-center">
                    <span className="text-xs text-dark-450 block">Consensus Confidence</span>
                    <strong className="text-dark-100 text-lg font-outfit block mt-0.5">{result.confidence_score}%</strong>
                  </div>
                  <div className="bg-dark-950/40 border border-dark-850 rounded-2xl p-4 text-center">
                    <span className="text-xs text-dark-450 block">Logistic Regression</span>
                    <span className={`text-sm font-semibold block mt-1 ${result.lr_classification === 'Harmful' ? 'text-red-400' : 'text-green-400'}`}>
                      {result.lr_classification} ({result.lr_confidence}%)
                    </span>
                  </div>
                  <div className="bg-dark-950/40 border border-dark-850 rounded-2xl p-4 text-center">
                    <span className="text-xs text-dark-450 block">SVM Classifier</span>
                    <span className={`text-sm font-semibold block mt-1 ${result.svm_classification === 'Harmful' ? 'text-red-400' : 'text-green-400'}`}>
                      {result.svm_classification} ({result.svm_confidence}%)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
