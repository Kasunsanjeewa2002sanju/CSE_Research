import React, { useState } from 'react';
import { History, Play, CheckCircle2, XCircle, ShieldCheck, Calendar, Activity, ArrowRight } from 'lucide-react';
import { api } from '../services/api';
import { BacktestResult } from '../types';
import { FanChart } from '../charts/FanChart';

const PRESET_CUTOFFS = [
  { label: '2022 Debt Default', date: '2022-04-12', family: 'Government Policy' },
  { label: '2022 Inflation Peak', date: '2022-06-30', family: 'Government Policy' },
  { label: '2022 Aragalaya Climax', date: '2022-07-09', family: 'Political Arrest' },
  { label: '2023 IMF Approval', date: '2023-03-20', family: 'Government Policy' },
  { label: '2024 Debt Restructure', date: '2024-06-26', family: 'Government Policy' },
];

export const Backtesting: React.FC = () => {
  const [cutoffDate, setCutoffDate] = useState('2022-04-12');
  const [eventFamily, setEventFamily] = useState('Government Policy');
  const [horizon, setHorizon] = useState(20);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunBacktest = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.runBacktest({
        cutoff_date: cutoffDate,
        event_family: eventFamily,
        target_symbol: 'ASPI',
        horizon_days: horizon
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Backtest replay failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <History className="w-6 h-6 text-blue-600" />
          Walk-Forward Historical Backtesting Lab
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Select any past date between 2020 and 2025 to simulate market conditions. All predictive models are strictly retrained with zero lookahead bias.
        </p>
      </div>

      {/* Preset Scenarios */}
      <div className="card p-5 shadow-sm space-y-3">
        <span className="text-xs font-semibold text-slate-500 block uppercase tracking-wider">
          Featured Historical Turning Points
        </span>
        <div className="flex flex-wrap gap-2">
          {PRESET_CUTOFFS.map((p) => {
            const active = cutoffDate === p.date && eventFamily === p.family;
            return (
              <button
                key={p.label}
                onClick={() => {
                  setCutoffDate(p.date);
                  setEventFamily(p.family);
                }}
                className={`text-xs px-3 py-1.5 rounded-lg font-medium transition ${
                  active
                    ? 'bg-blue-600 text-white font-bold shadow-xs'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200'
                }`}
              >
                {p.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Control Form & Status */}
      <div className="card p-5 shadow-sm space-y-4">
        <form onSubmit={handleRunBacktest} className="grid grid-cols-1 sm:grid-cols-5 gap-3 items-end">
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Historical Cutoff Date
            </label>
            <input
              type="date"
              value={cutoffDate}
              onChange={(e) => setCutoffDate(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 font-mono shadow-2xs"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Event Family
            </label>
            <select
              value={eventFamily}
              onChange={(e) => setEventFamily(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 shadow-2xs"
            >
              <option value="Government Policy">Government Policy</option>
              <option value="Political Arrest">Political Arrest</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Test Horizon
            </label>
            <select
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 shadow-2xs"
            >
              <option value={10}>10 Trading Days</option>
              <option value={20}>20 Trading Days (Default)</option>
              <option value={60}>60 Trading Days</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Market Instrument
            </label>
            <div className="bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-700 font-mono">
              ASPI (All Share)
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs transition flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
          >
            {loading ? <Activity className="w-4 h-4 animate-spin text-white" /> : <History className="w-4 h-4" />}
            {loading ? 'Replaying...' : 'Execute Backtest'}
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-brand-red text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-6">
          {/* Audit & Ground Truth KPI Header */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <div className="card p-4 shadow-sm">
              <span className="text-xs text-slate-500 font-medium">Predicted 20d Return</span>
              <div className={`text-xl font-bold font-mono mt-1 ${
                result.evaluation.predicted_return_pct >= 0 ? 'text-brand-green' : 'text-brand-red'
              }`}>
                {result.evaluation.predicted_return_pct > 0 ? `+${result.evaluation.predicted_return_pct}%` : `${result.evaluation.predicted_return_pct}%`}
              </div>
              <span className="text-[10px] text-slate-400 font-mono">Cutoff Model Output</span>
            </div>

            <div className="card p-4 shadow-sm">
              <span className="text-xs text-slate-500 font-medium">Actual Subsequent Return</span>
              <div className={`text-xl font-bold font-mono mt-1 ${
                (result.evaluation.actual_return_pct || 0) >= 0 ? 'text-brand-green' : 'text-brand-red'
              }`}>
                {result.evaluation.actual_return_pct !== null
                  ? `${result.evaluation.actual_return_pct > 0 ? '+' : ''}${result.evaluation.actual_return_pct}%`
                  : 'N/A'}
              </div>
              <span className="text-[10px] text-slate-400 font-mono">Actual CSE Ground Truth</span>
            </div>

            <div className="card p-4 shadow-sm">
              <span className="text-xs text-slate-500 font-medium">Direction Correctness</span>
              <div className="flex items-center gap-2 mt-1">
                {result.evaluation.direction_correct ? (
                  <>
                    <CheckCircle2 className="w-5 h-5 text-brand-green" />
                    <span className="text-lg font-bold text-brand-green">Accurate</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-5 h-5 text-brand-red" />
                    <span className="text-lg font-bold text-brand-red">Diverged</span>
                  </>
                )}
              </div>
              <span className="text-[10px] text-slate-400">Predicted vs Real Direction</span>
            </div>

            <div className="card p-4 shadow-sm">
              <span className="text-xs text-slate-500 font-medium">95% Interval Coverage</span>
              <div className="text-xl font-bold font-mono mt-1 text-blue-600">
                {result.evaluation.interval_coverage_pct}%
              </div>
              <span className="text-[10px] text-slate-400">Sessions inside 95% band</span>
            </div>
          </div>

          {/* Temporal Isolation Audit Card */}
          <div className="card p-4 flex items-center justify-between text-xs shadow-sm bg-emerald-50/70 border-emerald-200">
            <div className="flex items-center gap-3">
              <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0" />
              <div>
                <span className="font-bold text-emerald-950">Temporal Data Isolation Verified:</span>
                <p className="text-emerald-800 text-[11px]">
                  Zero future price or event leakage. Exactly {result.data_isolation_audit.future_events_excluded} post-cutoff political events were completely concealed from model training.
                </p>
              </div>
            </div>
            <span className="font-mono text-[11px] text-emerald-800 bg-emerald-100/80 px-2.5 py-1 rounded-md border border-emerald-300 font-medium">
              Cutoff: {result.parameters.aligned_cutoff_date}
            </span>
          </div>

          {/* Prediction Fan Chart vs Actual Ground Truth */}
          <div className="card p-6 shadow-sm space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Predicted Fan Chart vs. Actual Post-Cutoff CSE Performance
                </h3>
                <p className="text-xs text-slate-500">
                  Simulated event: <strong className="text-slate-800">{result.parameters.simulated_event.title}</strong> ({result.parameters.simulated_event.subtype})
                </p>
              </div>
              <span className="text-xs font-mono text-slate-500">
                Base Price: {result.cutoff_price.toLocaleString()} LKR
              </span>
            </div>

            <FanChart data={result.fan_chart} height="400px" />
          </div>
        </div>
      )}
    </div>
  );
};
