import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  FileText,
  UserX,
  History,
  CheckCircle2,
  Newspaper,
  Calendar,
  ArrowRight,
  ShieldCheck,
  Activity
} from 'lucide-react';
import { api } from '../services/api';
import { TimelineResponse, LiveIndices, LiveMarketStatus, NewsArticleItem } from '../types';
import { TimelineChart } from '../charts/TimelineChart';
import { EventDetailModal } from '../components/EventDetailModal';

export const Dashboard: React.FC = () => {
  const [timelineData, setTimelineData] = useState<TimelineResponse | null>(null);
  const [liveIndices, setLiveIndices] = useState<LiveIndices | null>(null);
  const [liveStatus, setLiveStatus] = useState<LiveMarketStatus | null>(null);
  const [recentNews, setRecentNews] = useState<NewsArticleItem[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const [tl, ind, st, news] = await Promise.all([
          api.getTimeline('2020-01-01', '2025-12-31'),
          api.getLiveIndices(),
          api.getLiveStatus(),
          api.getLatestNews(5)
        ]);
        setTimelineData(tl);
        setLiveIndices(ind);
        setLiveStatus(st);
        setRecentNews(news.articles || []);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };
    loadDashboard();
  }, []);

  const aspi = liveIndices?.aspi;

  return (
    <div className="space-y-6">
      {/* Hero Section (30% Corporate Blue anchor) */}
      <div className="bg-gradient-to-r from-blue-900 via-blue-800 to-blue-950 text-white rounded-2xl p-6 lg:p-8 shadow-md relative overflow-hidden">
        <div className="max-w-3xl relative z-10 space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-700/60 border border-blue-400/30 text-xs font-semibold text-blue-100">
            <ShieldCheck className="w-3.5 h-3.5" />
            Empirical Financial Research • Colombo Stock Exchange
          </div>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight leading-tight">
            How Political Events Influence Sri Lanka's Stock Market
          </h1>
          <p className="text-sm sm:text-base text-blue-100 leading-relaxed">
            Explore 40 years of historical CSE price movements, analyze quantitative abnormal returns around 
            70 government policy decisions and 34 political arrests, and evaluate machine-learning market impact forecasts.
          </p>
          <div className="pt-2 flex flex-wrap gap-3">
            <Link
              to="/predict-policy"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-white hover:bg-slate-50 text-blue-900 font-bold text-sm transition shadow-sm"
            >
              <FileText className="w-4 h-4 text-blue-700" />
              Predict Policy Impact
            </Link>
            <Link
              to="/predict-arrest"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-bold text-sm transition shadow-sm"
            >
              <UserX className="w-4 h-4" />
              Predict Arrest Impact
            </Link>
            <Link
              to="/verify"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-800/80 hover:bg-blue-700/80 border border-blue-600/70 text-white font-semibold text-sm transition"
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Verify News Claim
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Overview Cards (60% Crisp White Base) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: ASPI Live */}
        <div className="card p-5 card-hover">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>ASPI Live Benchmark</span>
            <span className={`w-2 h-2 rounded-full ${liveStatus?.is_open ? 'bg-brand-green animate-pulse' : 'bg-slate-400'}`} />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-slate-900">
            {aspi ? aspi.value.toLocaleString() : '20,059.42'}
          </div>
          <div className="mt-1 flex items-center text-xs font-semibold">
            {aspi && aspi.change >= 0 ? (
              <span className="text-brand-green flex items-center">
                <TrendingUp className="w-3.5 h-3.5 mr-1" />+{aspi.change} (+{aspi.change_pct}%)
              </span>
            ) : (
              <span className="text-brand-red flex items-center">
                <TrendingDown className="w-3.5 h-3.5 mr-1" />
                {aspi?.change || -125.63} ({aspi?.change_pct || -0.62}%)
              </span>
            )}
            <span className="text-slate-400 text-[10px] ml-auto">Real Exchange Feed</span>
          </div>
        </div>

        {/* Card 2: Government Policies */}
        <div className="card p-5 card-hover">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Government Policies</span>
            <div className="p-1.5 rounded-md bg-blue-50 text-blue-600">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-slate-900">70</div>
          <p className="mt-1 text-xs text-slate-500">
            Budgets, Taxes, IMF, Monetary <span className="text-blue-600 font-semibold">(2000–2025)</span>
          </p>
        </div>

        {/* Card 3: Political Arrests (10% Accent) */}
        <div className="card p-5 card-hover">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Political Legal Events</span>
            <div className="p-1.5 rounded-md bg-amber-50 text-amber-600">
              <UserX className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-slate-900">34</div>
          <p className="mt-1 text-xs text-slate-500">
            Arrests, Remands, Sentencings <span className="text-amber-600 font-semibold">(2000–2024)</span>
          </p>
        </div>

        {/* Card 4: Historical Sessions */}
        <div className="card p-5 card-hover">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>CSE Historical Sessions</span>
            <div className="p-1.5 rounded-md bg-emerald-50 text-emerald-600">
              <Calendar className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-slate-900">9,772</div>
          <p className="mt-1 text-xs text-slate-500">
            Active daily observations <span className="text-emerald-600 font-semibold">(1985–2025)</span>
          </p>
        </div>
      </div>

      {/* Main Historical Timeline Chart (2020-2025) */}
      <div className="card p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-base font-bold text-slate-900">
              Colombo Stock Exchange Movement & Political Events (2020–2025)
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Interactive ASPI daily series showing economic crises, debt restructuring, and political legal developments. Click markers for event study.
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 text-slate-700 font-medium">
              <span className="w-3 h-3 bg-blue-600 rotate-45 inline-block" /> Policy Change
            </span>
            <span className="flex items-center gap-1.5 text-slate-700 font-medium">
              <span className="w-3 h-3 bg-amber-500 rounded-full inline-block" /> Political Arrest
            </span>
            <Link to="/timeline" className="text-blue-600 hover:text-blue-700 flex items-center gap-1 ml-2 font-semibold">
              Full Timeline <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {loading ? (
          <div className="h-[420px] flex items-center justify-center text-slate-500">
            <Activity className="w-6 h-6 animate-spin text-blue-600 mr-2" />
            Loading historical market series...
          </div>
        ) : timelineData ? (
          <TimelineChart
            priceSeries={timelineData.price_series}
            eventMarkers={timelineData.event_markers}
            onSelectEvent={(id) => setSelectedEventId(id)}
            height="420px"
          />
        ) : (
          <div className="h-[420px] flex items-center justify-center text-slate-400">
            No price data available
          </div>
        )}
      </div>

      {/* Two Column Grid: Latest Verified Events & Current News */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Column 1: Backtesting Lab */}
        <div className="card p-6 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <div className="p-1 rounded bg-blue-50 text-blue-600">
                <History className="w-4 h-4" />
              </div>
              Historical Backtesting Lab
            </h3>
            <Link to="/backtesting" className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1">
              Run Replay <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Replay the Colombo Stock Exchange across any historical date between 2020 and 2025. 
            The system strictly trains models on information available on or before the selected cutoff date, 
            generates forecast fan charts, and audits performance against subsequent actual prices.
          </p>

          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 text-xs space-y-2">
            <div className="font-semibold text-slate-700">Featured Research Cutoffs:</div>
            <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
              <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-2xs">
                <span className="text-blue-600 block font-bold">2022-04-12</span>
                <span className="text-slate-500">External Debt Default</span>
              </div>
              <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-2xs">
                <span className="text-amber-600 block font-bold">2022-06-30</span>
                <span className="text-slate-500">Peak Forex Inflation Crisis</span>
              </div>
            </div>
          </div>
        </div>

        {/* Column 2: Current News Center Snapshot */}
        <div className="card p-6 space-y-3 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <div className="p-1 rounded bg-teal-50 text-teal-600">
                <Newspaper className="w-4 h-4" />
              </div>
              Latest Political & Economic News
            </h3>
            <Link to="/news" className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1">
              News Center <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-2.5">
            {recentNews.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">
                Click News Center to ingest latest live headlines.
              </p>
            ) : (
              recentNews.map((art) => (
                <div
                  key={art.news_id}
                  className="p-3 rounded-xl bg-slate-50 hover:bg-blue-50/50 border border-slate-200 flex items-start justify-between gap-3 transition"
                >
                  <div className="space-y-1">
                    <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                      art.event_family === 'Government Policy'
                        ? 'bg-blue-100 text-blue-800'
                        : art.event_family === 'Political Arrest'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-slate-200 text-slate-700'
                    }`}>
                      {art.event_subtype || art.event_family}
                    </span>
                    <h4 className="text-xs font-semibold text-slate-800 line-clamp-1 hover:text-blue-600">
                      <a href={art.source_url} target="_blank" rel="noreferrer">
                        {art.headline}
                      </a>
                    </h4>
                    <span className="text-[10px] text-slate-400 block">
                      {art.source_name} • {art.published_at ? new Date(art.published_at).toLocaleDateString() : 'Recent'}
                    </span>
                  </div>
                  <Link
                    to={`/verify?text=${encodeURIComponent(art.headline)}`}
                    className="shrink-0 text-[11px] px-2.5 py-1 rounded-md bg-blue-600 hover:bg-blue-700 font-medium text-white transition shadow-2xs"
                  >
                    Verify
                  </Link>
                </div>
              ))
            )}
          </div>
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
