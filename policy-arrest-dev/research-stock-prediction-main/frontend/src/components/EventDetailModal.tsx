import React, { useEffect, useState } from 'react';
import { X, ExternalLink, AlertCircle, Clock, Activity } from 'lucide-react';
import { api } from '../services/api';
import { EventDetail } from '../types';
import { BeforeAfterChart } from '../charts/BeforeAfterChart';

interface EventDetailModalProps {
  eventId: string | null;
  onClose: () => void;
}

export const EventDetailModal: React.FC<EventDetailModalProps> = ({ eventId, onClose }) => {
  const [detail, setDetail] = useState<EventDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!eventId) {
      setDetail(null);
      return;
    }
    setLoading(true);
    setError(null);
    api.getEventDetail(eventId)
      .then((data) => setDetail(data))
      .catch((err) => setError(err.message || 'Failed to load event'))
      .finally(() => setLoading(false));
  }, [eventId]);

  if (!eventId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fade-in">
      <div className="bg-white border border-slate-200 w-full max-w-4xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center gap-3">
            <span className={`px-2.5 py-1 rounded-md text-xs font-semibold uppercase tracking-wider ${
              detail?.event_family === 'Government Policy'
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : 'bg-amber-50 text-amber-800 border border-amber-300'
            }`}>
              {detail?.event_family || 'Political Event'}
            </span>
            <span className="text-xs font-mono text-slate-500 font-semibold">{eventId}</span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {loading && (
            <div className="py-20 flex flex-col items-center justify-center text-slate-500">
              <Activity className="w-8 h-8 animate-spin text-blue-600 mb-2" />
              <p className="text-sm">Retrieving event study abnormal returns...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-brand-red text-sm">
              {error}
            </div>
          )}

          {detail && !loading && (
            <>
              {/* Title & Metadata */}
              <div>
                <h2 className="text-xl font-bold text-slate-900 leading-snug">{detail.title}</h2>
                <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-slate-500">
                  <span className="flex items-center gap-1 font-mono">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    Market Reaction Session: <strong className="text-slate-800">{detail.aligned_date}</strong>
                  </span>
                  <span>•</span>
                  <span>Category: <strong className="text-slate-800">{detail.event_subtype}</strong></span>
                  {detail.cluster_id && (
                    <>
                      <span>•</span>
                      <span className="font-mono text-blue-600 font-medium">Temporal Cluster: {detail.cluster_id}</span>
                    </>
                  )}
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5">
                  <span className="text-xs text-slate-500 font-medium">1-Day CAR</span>
                  <div className={`text-xl font-bold mt-1 font-mono ${detail.car_0_1 >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                    {detail.car_0_1 > 0 ? `+${(detail.car_0_1 * 100).toFixed(2)}%` : `${(detail.car_0_1 * 100).toFixed(2)}%`}
                  </div>
                  <span className="text-[10px] text-slate-400">Immediate Shock</span>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5">
                  <span className="text-xs text-slate-500 font-medium">5-Day CAR</span>
                  <div className={`text-xl font-bold mt-1 font-mono ${detail.car_0_5 >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                    {detail.car_0_5 > 0 ? `+${(detail.car_0_5 * 100).toFixed(2)}%` : `${(detail.car_0_5 * 100).toFixed(2)}%`}
                  </div>
                  <span className="text-[10px] text-slate-400">Primary Horizon</span>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5">
                  <span className="text-xs text-slate-500 font-medium">20-Day CAR</span>
                  <div className={`text-xl font-bold mt-1 font-mono ${detail.car_0_20 >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                    {detail.car_0_20 > 0 ? `+${(detail.car_0_20 * 100).toFixed(2)}%` : `${(detail.car_0_20 * 100).toFixed(2)}%`}
                  </div>
                  <span className="text-[10px] text-slate-400">Medium-Term Drift</span>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5">
                  <span className="text-xs text-slate-500 font-medium">Turnover Ratio</span>
                  <div className="text-xl font-bold mt-1 font-mono text-blue-600">
                    {detail.turnover_shock_ratio}x
                  </div>
                  <span className="text-[10px] text-slate-400">vs 120d Baseline</span>
                </div>
              </div>

              {/* Trajectory Chart */}
              <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
                <h3 className="text-sm font-semibold text-slate-800 mb-2">
                  Market Trajectory Surrounding Event (t-10 to t+20 sessions)
                </h3>
                <BeforeAfterChart pricePath={detail.price_path} height="240px" />
              </div>

              {/* Summary description & context */}
              {detail.summary && (
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm text-slate-700 leading-relaxed">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                    Event Background & Context
                  </span>
                  {detail.summary}
                </div>
              )}

              {/* Sources */}
              {detail.sources && detail.sources.length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-2">
                    Verified Archival Sources
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {detail.sources.map((s, idx) => (
                      <a
                        key={idx}
                        href={s.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 border border-blue-200 text-xs font-medium text-blue-700 transition"
                      >
                        <span>{s.name || 'Primary Source'}</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Research Caution (10% Accent) */}
              <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <span>
                  <strong className="text-amber-950 font-semibold">Scientific Caution:</strong> {detail.interpretation_notice}
                </span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
