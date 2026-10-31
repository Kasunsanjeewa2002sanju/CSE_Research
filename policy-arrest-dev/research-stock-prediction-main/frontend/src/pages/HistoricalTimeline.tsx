import React, { useState, useEffect } from 'react';
import { Calendar, Filter, ArrowUpDown, Layers, RefreshCw, Activity } from 'lucide-react';
import { api } from '../services/api';
import { TimelineResponse } from '../types';
import { TimelineChart } from '../charts/TimelineChart';
import { EventDetailModal } from '../components/EventDetailModal';

const YEAR_PRESETS = [
  { label: 'All (2020–25)', from: '2020-01-01', to: '2025-12-31' },
  { label: '2022 Crisis', from: '2022-01-01', to: '2022-12-31' },
  { label: '2023 IMF Recovery', from: '2023-01-01', to: '2023-12-31' },
  { label: '2024 Stabilization', from: '2024-01-01', to: '2024-12-31' },
  { label: '2020 COVID Shock', from: '2020-01-01', to: '2020-12-31' },
];

export const HistoricalTimeline: React.FC = () => {
  const [dateFrom, setDateFrom] = useState('2020-01-01');
  const [dateTo, setDateTo] = useState('2025-12-31');
  const [selectedFamily, setSelectedFamily] = useState<string>('');
  const [selectedDirection, setSelectedDirection] = useState<string>('');
  const [timelineData, setTimelineData] = useState<TimelineResponse | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchTimeline = async () => {
    setLoading(true);
    try {
      const data = await api.getTimeline(
        dateFrom,
        dateTo,
        selectedFamily || undefined,
        undefined,
        selectedDirection || undefined
      );
      setTimelineData(data);
    } catch (err) {
      console.error('Failed to load timeline:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTimeline();
  }, [dateFrom, dateTo, selectedFamily, selectedDirection]);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Calendar className="w-6 h-6 text-blue-600" />
          Historical Market Timeline & Event Study Overlay
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Trace daily All Share Price Index (ASPI) prices with quantified Cumulative Abnormal Returns ($CAR$) across 104 verified political policy changes and arrests.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="card p-5 shadow-sm space-y-4">
        {/* Preset Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-500 font-semibold mr-1">Time Horizon:</span>
          {YEAR_PRESETS.map((p) => {
            const active = dateFrom === p.from && dateTo === p.to;
            return (
              <button
                key={p.label}
                onClick={() => {
                  setDateFrom(p.from);
                  setDateTo(p.to);
                }}
                className={`text-xs px-3 py-1.5 rounded-lg font-medium transition ${
                  active
                    ? 'bg-blue-600 text-white font-bold shadow-xs'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200'
                }`}
              >
                {p.label}
              </button>
            );
          })}
        </div>

        {/* Dropdown Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-3 border-t border-slate-100">
          <div>
            <label className="text-[11px] font-semibold text-slate-500 block mb-1">From Date</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 font-mono shadow-2xs"
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-500 block mb-1">To Date</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 font-mono shadow-2xs"
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-500 block mb-1">Event Family</label>
            <select
              value={selectedFamily}
              onChange={(e) => setSelectedFamily(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 shadow-2xs"
            >
              <option value="">All Political Events</option>
              <option value="Government Policy">Government Policy Changes (70)</option>
              <option value="Political Arrest">Political Legal Events (34)</option>
            </select>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-500 block mb-1">Market Reaction</label>
            <select
              value={selectedDirection}
              onChange={(e) => setSelectedDirection(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 shadow-2xs"
            >
              <option value="">All Market Directions</option>
              <option value="Positive">Positive (CAR &gt; +0.5%)</option>
              <option value="Negative">Negative (CAR &lt; -0.5%)</option>
              <option value="Neutral">Neutral / Flat</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Interactive Chart */}
      <div className="card p-6 shadow-sm space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>
            Displaying <strong className="text-slate-900">{timelineData?.total_sessions || 0}</strong> trading sessions and{' '}
            <strong className="text-blue-600 font-bold">{timelineData?.total_events_in_range || 0}</strong> political events
          </span>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 text-slate-700 font-medium">
              <span className="w-2.5 h-2.5 bg-blue-600 rotate-45 inline-block" /> Policy Change
            </span>
            <span className="flex items-center gap-1.5 text-slate-700 font-medium">
              <span className="w-2.5 h-2.5 bg-amber-500 rounded-full inline-block" /> Political Arrest
            </span>
          </div>
        </div>

        {loading ? (
          <div className="h-[480px] flex items-center justify-center text-slate-500">
            <Activity className="w-6 h-6 animate-spin text-blue-600 mr-2" />
            Loading timeline series...
          </div>
        ) : timelineData ? (
          <TimelineChart
            priceSeries={timelineData.price_series}
            eventMarkers={timelineData.event_markers}
            onSelectEvent={(id) => setSelectedEventId(id)}
            height="480px"
          />
        ) : null}
      </div>

      {/* Events Table in Selected Range */}
      <div className="card p-6 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <div className="p-1 rounded bg-blue-50 text-blue-600">
            <Layers className="w-4 h-4" />
          </div>
          Political Events in Selected Window ({timelineData?.event_markers.length || 0})
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase font-mono text-[10px] border-y border-slate-200">
              <tr>
                <th className="py-2.5 px-3">Date</th>
                <th className="py-2.5 px-3">Family</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Event Title</th>
                <th className="py-2.5 px-3 text-right">1d CAR</th>
                <th className="py-2.5 px-3 text-right">5d CAR</th>
                <th className="py-2.5 px-3 text-right">20d CAR</th>
                <th className="py-2.5 px-3 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {timelineData?.event_markers.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    No political events in the selected filter range.
                  </td>
                </tr>
              ) : (
                timelineData?.event_markers.map((em) => (
                  <tr key={em.event_id} className="hover:bg-slate-50 transition">
                    <td className="py-2.5 px-3 font-mono text-slate-900 font-medium">{em.aligned_date}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        em.event_family === 'Government Policy'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}>
                        {em.event_family === 'Government Policy' ? 'Policy' : 'Arrest'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">{em.event_subtype}</td>
                    <td className="py-2.5 px-3 font-medium text-slate-900 max-w-xs truncate">{em.title}</td>
                    <td className={`py-2.5 px-3 text-right font-mono font-semibold ${em.car_1d >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                      {em.car_1d > 0 ? `+${em.car_1d}%` : `${em.car_1d}%`}
                    </td>
                    <td className={`py-2.5 px-3 text-right font-mono font-semibold ${em.car_5d >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                      {em.car_5d > 0 ? `+${em.car_5d}%` : `${em.car_5d}%`}
                    </td>
                    <td className={`py-2.5 px-3 text-right font-mono font-semibold ${em.car_20d >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                      {em.car_20d > 0 ? `+${em.car_20d}%` : `${em.car_20d}%`}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <button
                        onClick={() => setSelectedEventId(em.event_id)}
                        className="px-2.5 py-1 rounded-md bg-blue-50 hover:bg-blue-600 hover:text-white text-blue-700 border border-blue-200 font-medium transition text-[11px]"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail Modal */}
      <EventDetailModal
        eventId={selectedEventId}
        onClose={() => setSelectedEventId(null)}
      />
    </div>
  );
};
