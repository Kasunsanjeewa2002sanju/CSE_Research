import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Search, 
  Filter, 
  Calendar, 
  Tag, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  ExternalLink, 
  Layers, 
  BookOpen, 
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';
import { EventDetailModal } from '../components/EventDetailModal';

interface EventCatalogItem {
  event_id: string;
  title: string;
  event_family: 'Government Policy' | 'Political Arrest';
  event_subtype: string;
  aligned_date: string;
  car_1d: number;
  car_5d: number;
  car_20d: number;
  impact_direction: 'Positive' | 'Negative' | 'Neutral';
  cluster_id?: string;
}

export const EventExplorer: React.FC = () => {
  const [searchKeyword, setSearchKeyword] = useState('');
  const [selectedFamily, setSelectedFamily] = useState<string>('');
  const [selectedSubtype, setSelectedSubtype] = useState<string>('');
  const [selectedDirection, setSelectedDirection] = useState<string>('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  // Summary query
  const { data: summaryData } = useQuery({
    queryKey: ['eventsSummary'],
    queryFn: () => api.getEventSummary()
  });

  // Events query
  const { data: eventsData, isLoading, refetch } = useQuery({
    queryKey: ['eventsCatalog', selectedFamily, selectedSubtype, dateFrom, dateTo, searchKeyword],
    queryFn: () => api.getEvents({
      family: selectedFamily || undefined,
      subtype: selectedSubtype || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      keyword: searchKeyword || undefined,
      limit: 150
    })
  });

  const events: EventCatalogItem[] = (eventsData?.events || []).filter((e: EventCatalogItem) => {
    if (!selectedDirection) return true;
    return e.impact_direction.toLowerCase() === selectedDirection.toLowerCase();
  });

  const clearFilters = () => {
    setSearchKeyword('');
    setSelectedFamily('');
    setSelectedSubtype('');
    setSelectedDirection('');
    setDateFrom('');
    setDateTo('');
  };

  const hasActiveFilters = Boolean(
    searchKeyword || selectedFamily || selectedSubtype || selectedDirection || dateFrom || dateTo
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-blue-600" />
            Verified Political Event Catalog
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Browse, search, and audit all 104 verified historical Sri Lankan political events (2020–2025) and their quantified abnormal returns (CAR) on the Colombo Stock Exchange (CSE).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-700 border border-blue-600 rounded-lg text-xs font-semibold text-white transition shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Catalog
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-5 flex items-center justify-between card-hover">
          <div>
            <span className="text-xs text-slate-500 uppercase font-semibold">Total Verified Events</span>
            <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
              {summaryData?.total_events ?? 104}
            </div>
            <span className="text-[11px] text-slate-400">70 Policies · 34 Arrests</span>
          </div>
          <div className="p-3 bg-blue-50 rounded-xl text-blue-600">
            <Layers className="w-6 h-6" />
          </div>
        </div>

        <div className="card p-5 flex items-center justify-between card-hover">
          <div>
            <span className="text-xs text-slate-500 uppercase font-semibold">Govt Policies Avg 5d CAR</span>
            <div className={`text-2xl font-bold font-mono mt-1 ${
              (summaryData?.by_family?.['Government Policy']?.mean_car_5d_pct ?? 0) >= 0
                ? 'text-brand-green'
                : 'text-brand-red'
            }`}>
              {summaryData?.by_family?.['Government Policy']?.mean_car_5d_pct !== undefined
                ? `${summaryData.by_family['Government Policy'].mean_car_5d_pct > 0 ? '+' : ''}${summaryData.by_family['Government Policy'].mean_car_5d_pct}%`
                : '-1.01%'}
            </div>
            <span className="text-[11px] text-slate-400">10 Sub-Categories</span>
          </div>
          <div className="p-3 bg-blue-50 rounded-xl text-blue-600">
            <Sparkles className="w-6 h-6" />
          </div>
        </div>

        <div className="card p-5 flex items-center justify-between card-hover">
          <div>
            <span className="text-xs text-slate-500 uppercase font-semibold">Political Arrests Avg 5d CAR</span>
            <div className={`text-2xl font-bold font-mono mt-1 ${
              (summaryData?.by_family?.['Political Arrest']?.mean_car_5d_pct ?? 0) >= 0
                ? 'text-brand-green'
                : 'text-brand-red'
            }`}>
              {summaryData?.by_family?.['Political Arrest']?.mean_car_5d_pct !== undefined
                ? `${summaryData.by_family['Political Arrest'].mean_car_5d_pct > 0 ? '+' : ''}${summaryData.by_family['Political Arrest'].mean_car_5d_pct}%`
                : '+0.44%'}
            </div>
            <span className="text-[11px] text-slate-400">7 Legal Action Subtypes</span>
          </div>
          <div className="p-3 bg-amber-50 rounded-xl text-amber-600">
            <Tag className="w-6 h-6" />
          </div>
        </div>

        <div className="card p-5 flex items-center justify-between card-hover">
          <div>
            <span className="text-xs text-slate-500 uppercase font-semibold">Catalog Filter Match</span>
            <div className="text-2xl font-bold font-mono text-blue-600 mt-1">
              {events.length}
            </div>
            <span className="text-[11px] text-slate-400">
              {hasActiveFilters ? 'Active filters applied' : 'Showing all records'}
            </span>
          </div>
          <div className="p-3 bg-slate-100 rounded-xl text-slate-600">
            <Filter className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="card p-5 space-y-4 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
          {/* Keyword Search */}
          <div className="md:col-span-4 relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              placeholder="Search by keywords, person, or category..."
              className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 shadow-2xs"
            />
          </div>

          {/* Family Filter */}
          <div className="md:col-span-2">
            <select
              value={selectedFamily}
              onChange={(e) => {
                setSelectedFamily(e.target.value);
                setSelectedSubtype('');
              }}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 shadow-2xs"
            >
              <option value="">All Families</option>
              <option value="Government Policy">Government Policy (70)</option>
              <option value="Political Arrest">Political Arrest (34)</option>
            </select>
          </div>

          {/* Subtype Filter */}
          <div className="md:col-span-3">
            <select
              value={selectedSubtype}
              onChange={(e) => setSelectedSubtype(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 shadow-2xs"
            >
              <option value="">All Subtypes / Categories</option>
              {summaryData?.subtypes_list?.map((sub: string) => (
                <option key={sub} value={sub}>
                  {sub}
                </option>
              ))}
            </select>
          </div>

          {/* Impact Direction Filter */}
          <div className="md:col-span-2">
            <select
              value={selectedDirection}
              onChange={(e) => setSelectedDirection(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 shadow-2xs"
            >
              <option value="">All Directions</option>
              <option value="Positive">Positive (CAR &gt; 0.5%)</option>
              <option value="Negative">Negative (CAR &lt; -0.5%)</option>
              <option value="Neutral">Neutral ([-0.5%, +0.5%])</option>
            </select>
          </div>

          {/* Clear Filters Button */}
          <div className="md:col-span-1">
            <button
              onClick={clearFilters}
              disabled={!hasActiveFilters}
              className={`w-full py-2 rounded-lg text-xs font-semibold transition ${
                hasActiveFilters
                  ? 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300'
                  : 'bg-slate-50 text-slate-400 border border-slate-200 cursor-not-allowed'
              }`}
            >
              Clear
            </button>
          </div>
        </div>

        {/* Date Filter Secondary Row */}
        <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-slate-100 text-xs">
          <div className="flex items-center gap-1.5 text-slate-500 font-medium">
            <Calendar className="w-3.5 h-3.5" />
            <span>Date Range:</span>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="bg-white border border-slate-300 rounded px-2 py-1 text-slate-800 text-xs focus:outline-none focus:border-blue-600 font-mono shadow-2xs"
            />
            <span className="text-slate-400">to</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="bg-white border border-slate-300 rounded px-2 py-1 text-slate-800 text-xs focus:outline-none focus:border-blue-600 font-mono shadow-2xs"
            />
          </div>
          {hasActiveFilters && (
            <span className="text-[11px] text-blue-600 font-semibold ml-auto">
              Showing {events.length} matched event records
            </span>
          )}
        </div>
      </div>

      {/* Events Table */}
      <div className="card overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900">
            Historical Events Study Dataset ({events.length})
          </h2>
          <span className="text-xs text-slate-500">
            Click any row to open the complete abnormal return breakdown & price path
          </span>
        </div>

        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center text-slate-500">
            <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mb-2" />
            <p className="text-xs">Loading historical event study repository...</p>
          </div>
        ) : events.length === 0 ? (
          <div className="py-16 text-center text-slate-500">
            <p className="text-sm font-medium">No historical events match the specified filter criteria.</p>
            <p className="text-xs mt-1">Try adjusting the search keywords, family, or date range.</p>
            <button
              onClick={clearFilters}
              className="mt-3 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded text-xs text-blue-700 font-semibold transition"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead className="border-b border-slate-200 bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider font-mono text-[10px]">
                <tr>
                  <th className="py-3 px-4">Event ID</th>
                  <th className="py-3 px-4">Trading Date</th>
                  <th className="py-3 px-4">Family / Subtype</th>
                  <th className="py-3 px-4">Headline / Description</th>
                  <th className="py-3 px-4 text-right">1-Day CAR</th>
                  <th className="py-3 px-4 text-right">5-Day CAR</th>
                  <th className="py-3 px-4 text-right">20-Day CAR</th>
                  <th className="py-3 px-4 text-center">Impact</th>
                  <th className="py-3 px-4 text-center">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {events.map((evt) => (
                  <tr
                    key={evt.event_id}
                    onClick={() => setSelectedEventId(evt.event_id)}
                    className="hover:bg-slate-50 cursor-pointer transition group"
                  >
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-500 font-semibold group-hover:text-blue-600">
                      {evt.event_id}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-800 whitespace-nowrap font-medium">
                      {evt.aligned_date}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="flex flex-col gap-1">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold w-max ${
                          evt.event_family === 'Government Policy'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}>
                          {evt.event_family}
                        </span>
                        <span className="text-[11px] text-slate-500">{evt.event_subtype}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 max-w-md">
                      <p className="text-slate-900 font-medium line-clamp-2 leading-relaxed">
                        {evt.title}
                      </p>
                      {evt.cluster_id && (
                        <span className="inline-block mt-1 text-[10px] text-blue-600 font-mono font-medium">
                          Cluster: {evt.cluster_id}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right font-mono whitespace-nowrap">
                      <span className={evt.car_1d >= 0 ? 'text-brand-green' : 'text-brand-red'}>
                        {evt.car_1d > 0 ? `+${evt.car_1d.toFixed(2)}%` : `${evt.car_1d.toFixed(2)}%`}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono whitespace-nowrap">
                      <span className={`font-semibold ${evt.car_5d >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                        {evt.car_5d > 0 ? `+${evt.car_5d.toFixed(2)}%` : `${evt.car_5d.toFixed(2)}%`}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono whitespace-nowrap">
                      <span className={evt.car_20d >= 0 ? 'text-brand-green' : 'text-brand-red'}>
                        {evt.car_20d > 0 ? `+${evt.car_20d.toFixed(2)}%` : `${evt.car_20d.toFixed(2)}%`}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center whitespace-nowrap">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium ${
                        evt.impact_direction === 'Positive'
                          ? 'bg-emerald-50 text-brand-green border border-emerald-200'
                          : evt.impact_direction === 'Negative'
                          ? 'bg-red-50 text-brand-red border border-red-200'
                          : 'bg-slate-100 text-slate-600 border border-slate-200'
                      }`}>
                        {evt.impact_direction === 'Positive' && <TrendingUp className="w-3 h-3" />}
                        {evt.impact_direction === 'Negative' && <TrendingDown className="w-3 h-3" />}
                        {evt.impact_direction === 'Neutral' && <Minus className="w-3 h-3" />}
                        {evt.impact_direction}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedEventId(evt.event_id);
                        }}
                        className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-blue-600 transition"
                        title="View Event Details & Trajectory"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Event Detail Modal */}
      <EventDetailModal
        eventId={selectedEventId}
        onClose={() => setSelectedEventId(null)}
      />
    </div>
  );
};
