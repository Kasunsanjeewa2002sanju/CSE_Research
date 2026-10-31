import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Clock } from 'lucide-react';
import { api } from '../services/api';
import { LiveIndices, LiveMarketStatus } from '../types';

export const Navbar: React.FC = () => {
  const [indices, setIndices] = useState<LiveIndices | null>(null);
  const [status, setStatus] = useState<LiveMarketStatus | null>(null);
  const [currentTime, setCurrentTime] = useState<string>('');

  useEffect(() => {
    // Clock
    const updateClock = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString('en-GB', { timeZone: 'Asia/Colombo' }));
    };
    updateClock();
    const clockInterval = setInterval(updateClock, 1000);

    // Fetch live indices and status
    const fetchMarketData = async () => {
      try {
        const [ind, st] = await Promise.all([
          api.getLiveIndices(),
          api.getLiveStatus()
        ]);
        setIndices(ind);
        setStatus(st);
      } catch (err) {
        console.warn('Live market header poll error:', err);
      }
    };

    fetchMarketData();
    const marketInterval = setInterval(fetchMarketData, 30000);

    return () => {
      clearInterval(clockInterval);
      clearInterval(marketInterval);
    };
  }, []);

  const aspi = indices?.aspi;
  const isUp = aspi ? aspi.change >= 0 : false;

  return (
    <header className="bg-white border-b border-slate-200/80 sticky top-0 z-40 px-4 lg:px-6 h-16 flex items-center justify-between shadow-xs">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white text-lg shadow-sm">
          PT
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg text-slate-900 tracking-tight">PolitiTrade</span>
            <span className="text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 border border-blue-200 font-bold uppercase tracking-wider">
              LK
            </span>
          </div>
          <p className="text-[11px] text-slate-500 hidden sm:block">AI-Powered CSE Political Impact Platform</p>
        </div>
      </div>

      {/* Live Market Bar */}
      <div className="flex items-center gap-3 md:gap-6">
        {/* Status indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-50 border border-slate-200 text-xs">
          <span className={`w-2 h-2 rounded-full ${status?.is_open ? 'bg-brand-green animate-pulse' : 'bg-slate-400'}`}></span>
          <span className="text-slate-700 font-medium">
            {status?.market_status || 'CSE Live'}
          </span>
          {status?.is_demo && (
            <span className="text-[10px] bg-amber-100 text-amber-800 border border-amber-200 px-1.5 py-0.2 rounded font-mono font-medium">DEMO</span>
          )}
        </div>

        {/* ASPI Snapshot */}
        {aspi && (
          <div className="flex items-center gap-2 text-sm font-mono bg-blue-50/60 px-3 py-1 rounded-lg border border-blue-200/70">
            <span className="text-slate-600 font-sans text-xs">ASPI:</span>
            <span className="font-bold text-slate-900">{aspi.value.toLocaleString()}</span>
            <span className={`flex items-center text-xs font-semibold ${isUp ? 'text-brand-green' : 'text-brand-red'}`}>
              {isUp ? <TrendingUp className="w-3.5 h-3.5 mr-0.5 inline" /> : <TrendingDown className="w-3.5 h-3.5 mr-0.5 inline" />}
              {aspi.change > 0 ? `+${aspi.change}` : aspi.change} ({aspi.change_pct > 0 ? `+${aspi.change_pct}%` : `${aspi.change_pct}%`})
            </span>
          </div>
        )}

        {/* Colombo Clock */}
        <div className="hidden lg:flex items-center gap-1.5 text-xs text-slate-500 font-mono">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>{currentTime} SLST</span>
        </div>
      </div>
    </header>
  );
};
