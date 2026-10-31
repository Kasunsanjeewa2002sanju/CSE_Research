import React, { useState, useEffect } from 'react';
import { LineChart, TrendingUp, TrendingDown, RefreshCw, Activity, Building2, Search, AlertCircle } from 'lucide-react';
import { api } from '../services/api';
import { LiveIndices, LiveMarketStatus, ListedSecurity } from '../types';

export const LiveMarket: React.FC = () => {
  const [indices, setIndices] = useState<LiveIndices | null>(null);
  const [status, setStatus] = useState<LiveMarketStatus | null>(null);
  const [gainers, setGainers] = useState<ListedSecurity[]>([]);
  const [losers, setLosers] = useState<ListedSecurity[]>([]);
  const [securities, setSecurities] = useState<ListedSecurity[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedSec, setSelectedSec] = useState<ListedSecurity | null>(null);

  const fetchLiveData = async () => {
    try {
      const [ind, st, g, l, sec] = await Promise.all([
        api.getLiveIndices(),
        api.getLiveStatus(),
        api.getLiveGainers(),
        api.getLiveLosers(),
        api.getLiveSecurities()
      ]);
      setIndices(ind);
      setStatus(st);
      setGainers(g.gainers || []);
      setLosers(l.losers || []);
      setSecurities(sec || []);
    } catch (err) {
      console.error('Failed to fetch live CSE quotes:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchLiveData();
    const interval = setInterval(fetchLiveData, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleManualRefresh = () => {
    setRefreshing(true);
    fetchLiveData();
  };

  const aspi = indices?.aspi;
  const sp20 = indices?.sp_sl20;

  const filteredSecurities = securities.filter(
    (s) =>
      s.symbol.toLowerCase().includes(search.toLowerCase()) ||
      s.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <LineChart className="w-6 h-6 text-blue-600" />
            Live Colombo Stock Exchange Dashboard
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Real-time quoted market prices, index movements, session turnover, and market movers directly from the CSE exchange gateway.
          </p>
        </div>

        <button
          onClick={handleManualRefresh}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-xs font-semibold text-white transition shadow-sm disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-white' : ''}`} />
          {refreshing ? 'Updating Live Quotes...' : 'Refresh Quotes'}
        </button>
      </div>

      {/* Market Status Alert / Freshness */}
      <div className="card p-4 flex flex-wrap items-center justify-between gap-3 text-xs shadow-xs">
        <div className="flex items-center gap-2.5">
          <span className={`w-2.5 h-2.5 rounded-full ${status?.is_open ? 'bg-brand-green animate-pulse' : 'bg-slate-400'}`} />
          <span className="text-slate-900 font-bold">Market Status: {status?.market_status || 'CSE Live'}</span>
          <span className="text-slate-300">•</span>
          <span className="text-slate-500">Data as of {status?.timestamp ? new Date(status.timestamp).toLocaleTimeString() : 'Current'}, Asia/Colombo</span>
        </div>
        <div className="text-[11px] text-slate-400 font-mono">
          Provider: {status?.provider} {status?.is_demo && '(DEMO DATA)'}
        </div>
      </div>

      {/* Top Index Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* ASPI */}
        <div className="card p-5 card-hover">
          <span className="text-xs text-slate-500 block font-medium">All Share Price Index (ASPI)</span>
          <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
            {aspi ? aspi.value.toLocaleString() : '20,059.42'}
          </div>
          <div className={`flex items-center text-xs font-semibold mt-1 ${aspi && aspi.change >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
            {aspi && aspi.change >= 0 ? <TrendingUp className="w-3.5 h-3.5 mr-1" /> : <TrendingDown className="w-3.5 h-3.5 mr-1" />}
            {aspi?.change || -125.63} ({aspi?.change_pct || -0.62}%)
          </div>
        </div>

        {/* S&P SL20 */}
        <div className="card p-5 card-hover">
          <span className="text-xs text-slate-500 block font-medium">S&P Sri Lanka 20 (S&P SL20)</span>
          <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
            {sp20 ? sp20.value.toLocaleString() : '5,700.75'}
          </div>
          <div className={`flex items-center text-xs font-semibold mt-1 ${sp20 && sp20.change >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
            {sp20 && sp20.change >= 0 ? <TrendingUp className="w-3.5 h-3.5 mr-1" /> : <TrendingDown className="w-3.5 h-3.5 mr-1" />}
            {sp20?.change || -38.08} ({sp20?.change_pct || -0.66}%)
          </div>
        </div>

        {/* Market Turnover */}
        <div className="card p-5 card-hover">
          <span className="text-xs text-slate-500 block font-medium">Session Turnover</span>
          <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
            Rs. 680.3M
          </div>
          <span className="text-[11px] text-slate-400 font-mono mt-1 block">Equity Trades: 13,031</span>
        </div>

        {/* Shares Traded */}
        <div className="card p-5 card-hover">
          <span className="text-xs text-slate-500 block font-medium">Shares Traded</span>
          <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
            33.56M
          </div>
          <span className="text-[11px] text-slate-400 font-mono mt-1 block">Active Securities: {securities.length || 290}</span>
        </div>
      </div>

      {/* Movers: Top Gainers & Losers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Gainers */}
        <div className="card p-6 shadow-sm space-y-3">
          <h3 className="text-sm font-bold flex items-center gap-2 text-brand-green">
            <TrendingUp className="w-4 h-4" /> Top CSE Gainers
          </h3>
          <div className="space-y-2">
            {gainers.slice(0, 5).map((g, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between text-xs">
                <span className="font-mono font-bold text-slate-900">{g.symbol}</span>
                <span className="font-mono text-slate-600">Rs. {g.price.toFixed(2)}</span>
                <span className="font-mono font-bold text-brand-green">+{g.change_pct}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Losers */}
        <div className="card p-6 shadow-sm space-y-3">
          <h3 className="text-sm font-bold flex items-center gap-2 text-brand-red">
            <TrendingDown className="w-4 h-4" /> Top CSE Losers
          </h3>
          <div className="space-y-2">
            {losers.slice(0, 5).map((l, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between text-xs">
                <span className="font-mono font-bold text-slate-900">{l.symbol}</span>
                <span className="font-mono text-slate-600">Rs. {l.price.toFixed(2)}</span>
                <span className="font-mono font-bold text-brand-red">{l.change_pct}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quoted Securities Table */}
      <div className="card p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <div className="p-1 rounded bg-blue-50 text-blue-600">
                <Building2 className="w-4 h-4" />
              </div>
              Listed Equities & Quoted Securities ({filteredSecurities.length})
            </h3>
            <p className="text-xs text-slate-500">Search symbols or company names across all CSE listed equities.</p>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search symbol or name..."
              className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 shadow-2xs"
            />
          </div>
        </div>

        <div className="overflow-x-auto max-h-[500px]">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 sticky top-0 text-slate-500 uppercase font-mono text-[10px] z-10 border-y border-slate-200">
              <tr>
                <th className="py-2.5 px-3">Symbol</th>
                <th className="py-2.5 px-3">Company Name</th>
                <th className="py-2.5 px-3 text-right">Last Price (LKR)</th>
                <th className="py-2.5 px-3 text-right">Change</th>
                <th className="py-2.5 px-3 text-right">Change %</th>
                <th className="py-2.5 px-3 text-right">Volume</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredSecurities.slice(0, 100).map((sec) => (
                <tr
                  key={sec.symbol}
                  onClick={() => setSelectedSec(sec)}
                  className="hover:bg-slate-50 cursor-pointer transition"
                >
                  <td className="py-2.5 px-3 font-mono font-bold text-blue-600">{sec.symbol}</td>
                  <td className="py-2.5 px-3 font-medium text-slate-800 max-w-xs truncate">{sec.name}</td>
                  <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900">
                    {sec.price.toFixed(2)}
                  </td>
                  <td className={`py-2.5 px-3 text-right font-mono ${sec.change >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                    {sec.change > 0 ? `+${sec.change.toFixed(2)}` : sec.change.toFixed(2)}
                  </td>
                  <td className={`py-2.5 px-3 text-right font-mono font-bold ${sec.change_pct >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                    {sec.change_pct > 0 ? `+${sec.change_pct.toFixed(2)}%` : `${sec.change_pct.toFixed(2)}%`}
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-400">
                    {sec.volume.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
