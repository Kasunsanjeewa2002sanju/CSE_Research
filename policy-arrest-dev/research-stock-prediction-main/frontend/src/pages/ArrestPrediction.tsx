import React, { useState } from 'react';
import { UserX, Activity, AlertCircle, ArrowRight, Layers, Scale, ExternalLink } from 'lucide-react';
import { api } from '../services/api';
import { PredictionResult } from '../types';
import { FanChart } from '../charts/FanChart';
import { EventDetailModal } from '../components/EventDetailModal';

const ARREST_SUBTYPES = [
  'Detention or Remand',
  'Corruption and Bribery Indictment',
  'Financial Crime and Money Laundering',
  'Civil Disobedience and Protest Action',
  'Abuse of Power and State Property',
  'Sentencing and Court Martial',
  'Contempt of Court and Bail Hearing'
];

export const ArrestPrediction: React.FC = () => {
  const [personName, setPersonName] = useState('');
  const [subtype, setSubtype] = useState(ARREST_SUBTYPES[0]);
  const [eventDesc, setEventDesc] = useState('');
  const [affiliation, setAffiliation] = useState('Opposition');
  const [crisis, setCrisis] = useState('No');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [horizon, setHorizon] = useState<number>(5);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedAnalogueId, setSelectedAnalogueId] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.predictArrest({
        person_name: personName,
        event_description: eventDesc,
        event_subtype: subtype,
        government_or_opposition: affiliation,
        announcement_date: date,
        crisis_or_protest: crisis,
        forecast_horizon: horizon
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to generate political arrest prediction');
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
          <UserX className="w-6 h-6 text-amber-600" />
          Political Legal Action & Arrest Impact Predictor
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Evaluate historical market behavior surrounding political arrests, detentions, corruption indictments, and legal proceedings.
        </p>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form */}
        <div className="lg:col-span-5 card p-6 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-2">
            <div className="p-1 rounded bg-amber-50 text-amber-600">
              <Scale className="w-4 h-4" />
            </div>
            Legal Event Parameters
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Political Figure / Entity Name
              </label>
              <input
                type="text"
                value={personName}
                onChange={(e) => setPersonName(e.target.value)}
                required
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-600 focus:ring-1 focus:ring-amber-600 shadow-2xs"
                placeholder="E.g., Former Cabinet Minister / Member of Parliament"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Legal Action Subtype
              </label>
              <select
                value={subtype}
                onChange={(e) => setSubtype(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-600 focus:ring-1 focus:ring-amber-600 shadow-2xs"
              >
                {ARREST_SUBTYPES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Allegation Context / Event Narrative
              </label>
              <textarea
                value={eventDesc}
                onChange={(e) => setEventDesc(e.target.value)}
                rows={3}
                required
                className="w-full bg-white border border-slate-300 rounded-lg p-3 text-xs text-slate-800 focus:outline-none focus:border-amber-600 focus:ring-1 focus:ring-amber-600 leading-relaxed shadow-2xs"
                placeholder="E.g., Detained under Emergency Regulations following street demonstrations..."
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Political Affiliation
                </label>
                <select
                  value={affiliation}
                  onChange={(e) => setAffiliation(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-600 focus:ring-1 focus:ring-amber-600 shadow-2xs"
                >
                  <option value="Opposition">Opposition</option>
                  <option value="Government">Government / Ruling Party</option>
                  <option value="Independent / Military">Independent / Security</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  State Crisis / Protest Link
                </label>
                <select
                  value={crisis}
                  onChange={(e) => setCrisis(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-600 focus:ring-1 focus:ring-amber-600 shadow-2xs"
                >
                  <option value="No">No (Standard Judicial Action)</option>
                  <option value="Yes">Yes (Associated with Unrest/Crisis)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Announcement / Action Date
                </label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-600 focus:ring-1 focus:ring-amber-600 font-mono shadow-2xs"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Horizon (Trading Days)
                </label>
                <select
                  value={horizon}
                  onChange={(e) => setHorizon(Number(e.target.value))}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-600 focus:ring-1 focus:ring-amber-600 shadow-2xs"
                >
                  <option value={1}>1 Trading Day</option>
                  <option value={5}>5 Trading Days</option>
                  <option value={10}>10 Trading Days</option>
                  <option value={20}>20 Trading Days</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-bold text-sm transition flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Activity className="w-4 h-4 animate-spin text-white" />
                  Analyzing Legal Precedents...
                </>
              ) : (
                'Analyze Political Legal Impact'
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
              <Scale className="w-12 h-12 text-slate-300 mx-auto" />
              <h3 className="text-base font-semibold text-slate-700">Awaiting Legal Action Submission</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Submit details regarding an arrest, detention, sentencing, or parliamentary action to evaluate
                historical CSE precedents and model-estimated abnormal market returns.
              </p>
            </div>
          )}

          {result && (
            <>
              {/* Primary Card */}
              <div className="card p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div>
                    <span className="text-xs text-slate-500 font-medium">Market Response Outlook ({result.forecast_horizon})</span>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-2xl font-extrabold tracking-tight ${
                        isUp ? 'text-brand-green' : isDown ? 'text-brand-red' : 'text-slate-800'
                      }`}>
                        {result.predicted_direction}
                      </span>
                      <span className="px-2.5 py-0.5 rounded-md text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                        {result.confidence_level} Confidence
                      </span>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-xs text-slate-500 font-medium">Expected 5d CAR</span>
                    <div className={`text-2xl font-extrabold font-mono mt-1 ${
                      result.expected_return_pct >= 0 ? 'text-brand-green' : 'text-brand-red'
                    }`}>
                      {result.expected_return_pct > 0 ? `+${result.expected_return_pct}%` : `${result.expected_return_pct}%`}
                    </div>
                  </div>
                </div>

                <div className="p-3.5 bg-amber-50/50 border border-amber-200/70 rounded-xl text-xs text-slate-700 leading-relaxed">
                  <span className="font-semibold text-amber-950 block mb-1">Precedent Summary:</span>
                  {result.explanation}
                </div>

                {/* Horizon breakdown */}
                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                  {Object.entries(result.horizons_breakdown).map(([hKey, vals]) => (
                    <div key={hKey} className="bg-slate-50 border border-slate-200 rounded-xl p-2.5">
                      <span className="text-slate-500 uppercase font-mono text-[10px] block font-semibold">{hKey}</span>
                      <span className={`font-mono font-bold text-sm mt-0.5 block ${vals.expected_car_pct >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                        {vals.expected_car_pct > 0 ? `+${vals.expected_car_pct}%` : `${vals.expected_car_pct}%`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Fan Chart */}
              {result.fan_chart && (
                <div className="card p-6 shadow-sm space-y-3">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <div className="p-1 rounded bg-amber-50 text-amber-600">
                      <Activity className="w-4 h-4" />
                    </div>
                    Estimated Market Evolution
                  </h3>
                  <FanChart data={result.fan_chart} height="320px" />
                </div>
              )}

              {/* Precedents */}
              <div className="card p-6 shadow-sm space-y-3">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <div className="p-1 rounded bg-amber-50 text-amber-600">
                    <Layers className="w-4 h-4" />
                  </div>
                  Historical Political Precedents
                </h3>
                <div className="space-y-2">
                  {result.similar_events.map((ev) => (
                    <div
                      key={ev.event_id}
                      onClick={() => setSelectedAnalogueId(ev.event_id)}
                      className="p-3.5 bg-slate-50 hover:bg-amber-50/50 border border-slate-200 rounded-xl cursor-pointer transition flex items-center justify-between gap-3 shadow-2xs"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-semibold font-mono">
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
