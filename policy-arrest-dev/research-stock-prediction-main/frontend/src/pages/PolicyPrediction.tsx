import React, { useState } from 'react';
import { FileText, Activity, AlertCircle, ArrowRight, Layers, Sliders, ExternalLink } from 'lucide-react';
import { api } from '../services/api';
import { PredictionResult } from '../types';
import { FanChart } from '../charts/FanChart';
import { EventDetailModal } from '../components/EventDetailModal';

const POLICY_CATEGORIES = [
  'Monetary Policy and Interest Rates',
  'Fiscal Policy, Budgets, and Taxation',
  'IMF Program and Debt Restructuring',
  'Fuel, Energy, and Electricity Tariffs',
  'Trade, Tariffs, and Import Restrictions',
  'Foreign Exchange and Currency Controls',
  'Agricultural Policy and Fertilizer Subsidies',
  'Capital Markets Regulation and SEC Rules',
  'State-Owned Enterprise Reforms and Privatization',
  'Crisis Emergency and Curfew Measures'
];

const SECTORS_LIST = [
  'Banking & Financial Services',
  'Consumer Staples & Retail',
  'Energy & Utilities',
  'Manufacturing & Industrials',
  'Tourism & Hospitality',
  'Plantations & Agriculture',
  'Construction & Real Estate'
];

export const PolicyPrediction: React.FC = () => {
  const [policyType, setPolicyType] = useState(POLICY_CATEGORIES[1]);
  const [headline, setHeadline] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedSectors, setSelectedSectors] = useState<string[]>(['Banking & Financial Services']);
  const [horizon, setHorizon] = useState<number>(5);
  const [historicalCutoff, setHistoricalCutoff] = useState<string>('');

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedAnalogueId, setSelectedAnalogueId] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.predictPolicy({
        policy_type: policyType,
        policy_headline: headline,
        announcement_date: date,
        affected_sectors: selectedSectors,
        target_symbol: 'ASPI',
        forecast_horizon: horizon,
        historical_cutoff: historicalCutoff || undefined
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to generate policy prediction');
    } finally {
      setLoading(false);
    }
  };

  const isUp = result?.predicted_direction === 'Positive';
  const isDown = result?.predicted_direction === 'Negative';

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <FileText className="w-6 h-6 text-blue-600" />
          Government Policy Impact Predictor
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Explore how Sri Lankan government decisions have historically affected the stock market and estimate potential reactions.
        </p>
      </div>

      {/* Two Column Layout: Form & Results */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form */}
        <div className="lg:col-span-5 card p-6 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-2">
            <div className="p-1 rounded bg-blue-50 text-blue-600">
              <Sliders className="w-4 h-4" />
            </div>
            Policy Parameters
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Policy Category Taxonomy
              </label>
              <select
                value={policyType}
                onChange={(e) => setPolicyType(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 shadow-2xs"
              >
                {POLICY_CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Policy Headline / Narrative Description
              </label>
              <textarea
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                rows={3}
                required
                className="w-full bg-white border border-slate-300 rounded-lg p-3 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 leading-relaxed shadow-2xs"
                placeholder="E.g., Central Bank implements statutory reserve ratio adjustment..."
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Announcement Date
                </label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 font-mono shadow-2xs"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Forecast Horizon
                </label>
                <select
                  value={horizon}
                  onChange={(e) => setHorizon(Number(e.target.value))}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 shadow-2xs"
                >
                  <option value={1}>1 Trading Day (Immediate)</option>
                  <option value={5}>5 Trading Days (1 Week)</option>
                  <option value={10}>10 Trading Days (2 Weeks)</option>
                  <option value={20}>20 Trading Days (1 Month)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Exposed Economic Sectors
              </label>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {SECTORS_LIST.map((sec) => {
                  const sel = selectedSectors.includes(sec);
                  return (
                    <button
                      type="button"
                      key={sec}
                      onClick={() => {
                        setSelectedSectors(
                          sel ? selectedSectors.filter((s) => s !== sec) : [...selectedSectors, sec]
                        );
                      }}
                      className={`text-[11px] px-2.5 py-1 rounded-md transition ${
                        sel
                          ? 'bg-blue-600 text-white font-medium shadow-2xs'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200 border border-slate-200'
                      }`}
                    >
                      {sec}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5 mb-1">
                <span>Historical Backtest Cutoff (Optional)</span>
                <span className="text-[10px] text-slate-400 font-normal">Excludes data after date</span>
              </label>
              <input
                type="date"
                value={historicalCutoff}
                onChange={(e) => setHistoricalCutoff(e.target.value)}
                placeholder="YYYY-MM-DD"
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 font-mono shadow-2xs"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm transition flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Activity className="w-4 h-4 animate-spin text-white" />
                  Running Predictive Models...
                </>
              ) : (
                'Analyze Policy Impact'
              )}
            </button>
          </form>
        </div>

        {/* Right Output */}
        <div className="lg:col-span-7 space-y-5">
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-brand-red text-sm">
              {error}
            </div>
          )}

          {!result && !loading && !error && (
            <div className="card p-12 text-center text-slate-400 space-y-3">
              <FileText className="w-12 h-12 text-slate-300 mx-auto" />
              <h3 className="text-base font-semibold text-slate-700">Awaiting Policy Input</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Submit a government policy announcement to evaluate empirical market reaction probabilities, 
                expected Cumulative Abnormal Return (CAR), uncertainty bounds, and historical analogues.
              </p>
            </div>
          )}

          {result && (
            <>
              {/* Primary Prediction KPI Card */}
              <div className="card p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div>
                    <span className="text-xs text-slate-500 font-medium">Predicted Market Tendency ({result.forecast_horizon})</span>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-2xl font-extrabold tracking-tight ${
                        isUp ? 'text-brand-green' : isDown ? 'text-brand-red' : 'text-slate-800'
                      }`}>
                        {result.predicted_direction}
                      </span>
                      <span className={`px-2.5 py-0.5 rounded-md text-xs font-semibold ${
                        result.confidence_level === 'High'
                          ? 'bg-emerald-50 text-brand-green border border-emerald-200'
                          : result.confidence_level === 'Medium'
                          ? 'bg-amber-50 text-amber-800 border border-amber-200'
                          : 'bg-slate-100 text-slate-700'
                      }`}>
                        {result.confidence_level} Confidence
                      </span>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-xs text-slate-500 font-medium">Expected 5d Return</span>
                    <div className={`text-2xl font-extrabold font-mono mt-1 ${
                      result.expected_return_pct >= 0 ? 'text-brand-green' : 'text-brand-red'
                    }`}>
                      {result.expected_return_pct > 0 ? `+${result.expected_return_pct}%` : `${result.expected_return_pct}%`}
                    </div>
                  </div>
                </div>

                {/* Horizon Breakdown Grid */}
                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                  {Object.entries(result.horizons_breakdown).map(([hKey, vals]) => (
                    <div key={hKey} className="bg-slate-50 border border-slate-200 rounded-xl p-2.5">
                      <span className="text-slate-500 uppercase font-mono text-[10px] block font-semibold">{hKey} Outlook</span>
                      <span className={`font-mono font-bold text-sm mt-0.5 block ${vals.expected_car_pct >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                        {vals.expected_car_pct > 0 ? `+${vals.expected_car_pct}%` : `${vals.expected_car_pct}%`}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        [{vals.lower_bound_pct}%, {vals.upper_bound_pct}%]
                      </span>
                    </div>
                  ))}
                </div>

                {/* Explanation */}
                <div className="p-3.5 bg-blue-50/50 border border-blue-200/70 rounded-xl text-xs text-slate-700 leading-relaxed">
                  <span className="font-semibold text-slate-900 block mb-1">Empirical Synthesis:</span>
                  {result.explanation}
                </div>
              </div>

              {/* Fan Chart Projection */}
              {result.fan_chart && (
                <div className="card p-6 shadow-sm space-y-3">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <div className="p-1 rounded bg-blue-50 text-blue-600">
                      <Activity className="w-4 h-4" />
                    </div>
                    Probabilistic Index Path Projection (Fan Chart)
                  </h3>
                  <FanChart data={result.fan_chart} height="320px" />
                </div>
              )}

              {/* Historical Precedents */}
              <div className="card p-6 shadow-sm space-y-3">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <div className="p-1 rounded bg-blue-50 text-blue-600">
                    <Layers className="w-4 h-4" />
                  </div>
                  Historical Precedent Analogues (Model 1 Precedents)
                </h3>
                <div className="space-y-2">
                  {result.similar_events.map((ev) => (
                    <div
                      key={ev.event_id}
                      onClick={() => setSelectedAnalogueId(ev.event_id)}
                      className="p-3.5 bg-slate-50 hover:bg-blue-50/60 border border-slate-200 rounded-xl cursor-pointer transition flex items-center justify-between gap-3 shadow-2xs"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-semibold font-mono">
                            {ev.similarity_score}% Match
                          </span>
                          <span className="text-xs font-mono text-slate-500">{ev.aligned_date}</span>
                        </div>
                        <h4 className="text-xs font-semibold text-slate-800">{ev.title}</h4>
                      </div>
                      <div className="text-right shrink-0">
                        <span className={`text-xs font-bold font-mono ${ev.car_5d >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                          5d CAR: {ev.car_5d > 0 ? `+${ev.car_5d}%` : `${ev.car_5d}%`}
                        </span>
                        <span className="text-[10px] text-slate-400 block">Click to inspect</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      <EventDetailModal
        eventId={selectedAnalogueId}
        onClose={() => setSelectedAnalogueId(null)}
      />
    </div>
  );
};
