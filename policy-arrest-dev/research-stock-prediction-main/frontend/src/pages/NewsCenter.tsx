import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Newspaper, ExternalLink, RefreshCw, CheckCircle2, Activity, Filter } from 'lucide-react';
import { api } from '../services/api';
import { NewsArticleItem } from '../types';

export const NewsCenter: React.FC = () => {
  const [articles, setArticles] = useState<NewsArticleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(false);
  const [selectedFamily, setSelectedFamily] = useState<string>('');
  const [message, setMessage] = useState<string | null>(null);

  const fetchArticles = async () => {
    setLoading(true);
    try {
      const data = await api.getLatestNews(50, selectedFamily || undefined);
      setArticles(data.articles || []);
    } catch (err) {
      console.error('Failed to load news:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArticles();
  }, [selectedFamily]);

  const handlePoll = async () => {
    setPolling(true);
    setMessage(null);
    try {
      const res = await api.pollNews();
      setMessage(`Feed poll completed. Ingested ${res.new_articles_ingested} new articles.`);
      fetchArticles();
    } catch (err: any) {
      setMessage(`Poll failed: ${err.message}`);
    } finally {
      setPolling(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Newspaper className="w-6 h-6 text-blue-600" />
            Current News Center
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Real-time political and economic news ingested from verified Sri Lankan publishers and regulatory feeds.
          </p>
        </div>

        <button
          onClick={handlePoll}
          disabled={polling}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-xs font-semibold text-white transition shadow-sm disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${polling ? 'animate-spin text-white' : ''}`} />
          {polling ? 'Polling Active Feeds...' : 'Poll News Feeds'}
        </button>
      </div>

      {message && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-800 font-medium">
          {message}
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-3">
        <span className="text-xs text-slate-500 font-semibold mr-2 flex items-center gap-1">
          <Filter className="w-3.5 h-3.5" /> Filter Category:
        </span>
        {[
          { label: 'All News', value: '' },
          { label: 'Government Policies', value: 'Government Policy' },
          { label: 'Political Arrests & Legal', value: 'Political Arrest' },
          { label: 'General Macroeconomic', value: 'Other News' },
        ].map((tab) => {
          const active = selectedFamily === tab.value;
          return (
            <button
              key={tab.label}
              onClick={() => setSelectedFamily(tab.value)}
              className={`text-xs px-3 py-1.5 rounded-lg font-medium transition ${
                active
                  ? 'bg-blue-600 text-white font-bold shadow-xs'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Articles Grid */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center text-slate-500">
          <Activity className="w-8 h-8 animate-spin text-blue-600 mb-2" />
          <p className="text-sm">Retrieving stored news articles...</p>
        </div>
      ) : articles.length === 0 ? (
        <div className="card p-12 text-center text-slate-400 space-y-3">
          <Newspaper className="w-12 h-12 text-slate-300 mx-auto" />
          <h3 className="text-base font-semibold text-slate-700">No Articles Ingested Yet</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Click 'Poll News Feeds' above to fetch latest headlines from CBSL, Daily FT, EconomyNext, and Newsfirst.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {articles.map((art) => (
            <div
              key={art.news_id}
              className="card p-5 card-hover flex flex-col justify-between"
            >
              <div className="space-y-2.5">
                <div className="flex items-center justify-between text-[11px]">
                  <span className={`px-2 py-0.5 rounded font-medium ${
                    art.event_family === 'Government Policy'
                      ? 'bg-blue-100 text-blue-800'
                      : art.event_family === 'Political Arrest'
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {art.event_subtype || art.event_family}
                  </span>
                  <span className="text-slate-400 font-mono text-[10px]">
                    Tier {art.source_tier} Publisher
                  </span>
                </div>

                <h3 className="text-sm font-bold text-slate-900 hover:text-blue-600 leading-snug">
                  <a href={art.source_url} target="_blank" rel="noreferrer" className="flex items-start gap-1">
                    <span>{art.headline}</span>
                    <ExternalLink className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                  </a>
                </h3>

                {art.summary && (
                  <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                    {art.summary}
                  </p>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                <div className="text-[11px] text-slate-500">
                  <span className="text-slate-700 font-medium block">{art.source_name}</span>
                  <span>{art.published_at ? new Date(art.published_at).toLocaleDateString() : 'Recent'}</span>
                </div>

                <Link
                  to={`/verify?text=${encodeURIComponent(art.headline)}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-600 hover:text-white border border-blue-200 text-xs font-semibold text-blue-700 transition"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Verify Claim
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
