import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle, ShieldCheck, ExternalLink, Activity, Layers, FileText } from 'lucide-react';
import { api } from '../services/api';
import { VerificationResponse } from '../types';

export const NewsVerification: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialText = searchParams.get('text') || '';

  const [inputText, setInputText] = useState(initialText);
  const [inputUrl, setInputUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VerificationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialText) {
      handleVerify(initialText, '');
    }
  }, [initialText]);

  const handleVerify = async (text: string, url: string) => {
    if (!text && !url) {
      setError('Please provide a news headline or URL to verify.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.verifyNews({
        headline_or_text: text || undefined,
        article_url: url || undefined
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Verification execution failed');
    } finally {
      setLoading(false);
    }
  };

  const getVerdictBadge = (verdict: string) => {
    if (verdict.includes('Confirmed')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-300">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Confirmed by Credible Reporting
        </span>
      );
    }
    if (verdict.includes('Partially')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-300">
          <AlertTriangle className="w-4 h-4 text-amber-600" /> Partially Corroborated
        </span>
      );
    }
    if (verdict.includes('Contradicted')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-800 border border-red-300">
          <XCircle className="w-4 h-4 text-red-600" /> Contradicted by Evidence
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-300">
        <HelpCircle className="w-4 h-4 text-slate-500" /> Unverified Claim
      </span>
    );
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <CheckCircle2 className="w-6 h-6 text-blue-600" />
          News Claim Verification & Scenario Lab
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Verify user-submitted news stories against trusted Sri Lankan publishers and regulatory sources. 
          Evaluate twin conditional scenarios: What if the event is factual vs. what if it does not occur?
        </p>
      </div>

      {/* Submission Box */}
      <div className="card p-6 shadow-sm space-y-4">
        <div className="space-y-3">
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              News Headline or Descriptive Text Claim
            </label>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              rows={3}
              placeholder="Paste a news headline, WhatsApp rumor, or statement to verify..."
              className="w-full bg-white border border-slate-300 rounded-lg p-3 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 leading-relaxed shadow-2xs"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Article Web Link (Optional — Protected by SSRF Validation)
            </label>
            <input
              type="url"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              placeholder="https://www.ft.lk/financial-services/... or other public news link"
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 font-mono shadow-2xs"
            />
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
            <span className="text-[11px] text-slate-400">
              Matches against Central Bank, Ministry of Finance, CSE, Daily FT, Reuters, EconomyNext, etc.
            </span>
            <button
              onClick={() => handleVerify(inputText, inputUrl)}
              disabled={loading}
              className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs transition flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
            >
              {loading ? <Activity className="w-4 h-4 animate-spin text-white" /> : <CheckCircle2 className="w-4 h-4" />}
              {loading ? 'Verifying Evidence...' : 'Verify This News'}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-brand-red text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-6">
          {/* Verdict Box */}
          <div className="card p-6 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
              <div>
                <span className="text-xs text-slate-500 block mb-1">Verification Decision:</span>
                {getVerdictBadge(result.verdict)}
              </div>

              <div className="text-right">
                <span className="text-xs text-slate-500 block">Heuristic Evidence Score</span>
                <span className="text-2xl font-bold font-mono text-blue-600">
                  {Math.round(result.heuristic_evidence_score * 100)}%
                </span>
                <span className="text-[10px] text-slate-400 block">Empirical Corroboration</span>
              </div>
            </div>

            {/* Explanation & Claim summary */}
            <div className="space-y-3">
              <div className="text-sm text-slate-800 leading-relaxed font-medium">
                {result.explanation}
              </div>

              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1.5">
                <span className="text-slate-500 font-semibold block">Analyzed Claim:</span>
                <p className="text-slate-900 font-serif italic text-sm">"{result.claim_summary}"</p>
                <div className="flex flex-wrap gap-3 pt-2 text-[11px] text-slate-500">
                  <span>Detected Category: <strong className="text-blue-600">{result.detected_event_subtype}</strong></span>
                  {result.entities_detected.length > 0 && (
                    <span>Entities: <strong className="text-slate-800">{result.entities_detected.join(', ')}</strong></span>
                  )}
                  {result.institutions_detected.length > 0 && (
                    <span>Institutions: <strong className="text-slate-800">{result.institutions_detected.join(', ')}</strong></span>
                  )}
                </div>
              </div>
            </div>

            {/* Matched Evidence List */}
            {result.matched_evidence.length > 0 && (
              <div className="space-y-2 pt-2">
                <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider block">
                  Matched Published Evidence ({result.matched_evidence.length})
                </span>
                <div className="space-y-2">
                  {result.matched_evidence.map((ev, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-start justify-between gap-4"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                            Tier {ev.source_tier}
                          </span>
                          <span className="text-xs font-semibold text-slate-800">{ev.source_name}</span>
                          <span className="text-[10px] text-slate-400">• {ev.published_at}</span>
                        </div>
                        <h4 className="text-xs font-medium text-slate-700">{ev.headline}</h4>
                      </div>
                      <a
                        href={ev.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="shrink-0 p-1.5 rounded hover:bg-slate-200 text-slate-400 hover:text-blue-600 transition"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Conditional Scenarios */}
          {result.scenarios && (
            <div className="space-y-3">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <div className="p-1 rounded bg-blue-50 text-blue-600">
                  <Layers className="w-4 h-4" />
                </div>
                Conditional Stock Market Impact Scenarios
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Scenario A: If Event Occurs */}
                <div className="card p-6 border-blue-200 shadow-sm space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <div>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-blue-600">
                        Scenario A
                      </span>
                      <h3 className="text-sm font-bold text-slate-900">
                        If Reported Event is True / Occurs
                      </h3>
                    </div>
                    <span className="text-xs px-2.5 py-0.5 rounded bg-blue-100 text-blue-800 font-semibold font-mono">
                      Event Shock Active
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-center">
                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
                      <span className="text-[10px] text-slate-500 block font-semibold">Expected 5d Impact</span>
                      <span className={`text-xl font-bold font-mono mt-0.5 block ${
                        result.scenarios.scenario_a_true.expected_return_pct >= 0 ? 'text-brand-green' : 'text-brand-red'
                      }`}>
                        {result.scenarios.scenario_a_true.expected_return_pct > 0
                          ? `+${result.scenarios.scenario_a_true.expected_return_pct}%`
                          : `${result.scenarios.scenario_a_true.expected_return_pct}%`}
                      </span>
                    </div>

                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
                      <span className="text-[10px] text-slate-500 block font-semibold">95% Range</span>
                      <span className="text-xs font-bold font-mono mt-1 block text-slate-700">
                        [{result.scenarios.scenario_a_true.interval_lower_pct}%, {result.scenarios.scenario_a_true.interval_upper_pct}%]
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-500 leading-relaxed">
                    Applies model-estimated event shock derived from historical precedents in the {result.detected_event_subtype} category.
                  </p>
                </div>

                {/* Scenario B: If Event Does Not Occur */}
                <div className="card p-6 border-slate-200 shadow-sm space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <div>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                        Scenario B
                      </span>
                      <h3 className="text-sm font-bold text-slate-900">
                        No-Event Baseline (If False or Unshocked)
                      </h3>
                    </div>
                    <span className="text-xs px-2.5 py-0.5 rounded bg-slate-100 text-slate-600 font-semibold font-mono">
                      Baseline Drift
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-center">
                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
                      <span className="text-[10px] text-slate-500 block font-semibold">Expected Return</span>
                      <span className="text-xl font-bold font-mono mt-0.5 block text-slate-700">
                        0.00% (Drift)
                      </span>
                    </div>

                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
                      <span className="text-[10px] text-slate-500 block font-semibold">95% Market Vol Band</span>
                      <span className="text-xs font-bold font-mono mt-1 block text-slate-700">
                        [{result.scenarios.scenario_b_false.interval_lower_pct}%, +{result.scenarios.scenario_b_false.interval_upper_pct}%]
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-500 leading-relaxed">
                    {result.scenarios.scenario_b_false.scientific_notice}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
