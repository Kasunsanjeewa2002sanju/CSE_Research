import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Calendar,
  FileText,
  UserX,
  History,
  Newspaper,
  CheckCircle2,
  LineChart,
  Layers,
  BookOpen
} from 'lucide-react';

const NAV_ITEMS = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Historical Timeline', path: '/timeline', icon: Calendar, badge: '2020–25' },
  { name: 'Policy Predictor', path: '/predict-policy', icon: FileText },
  { name: 'Arrest Predictor', path: '/predict-arrest', icon: UserX },
  { name: 'Backtesting Lab', path: '/backtesting', icon: History, badge: 'Replay' },
  { name: 'News Center', path: '/news', icon: Newspaper },
  { name: 'Verify News', path: '/verify', icon: CheckCircle2, badge: 'AI', badgeAccent: true },
  { name: 'Live CSE Market', path: '/live', icon: LineChart, badge: 'Real' },
  { name: 'Event Explorer', path: '/events', icon: Layers, badge: '104' },
  { name: 'Model & Research', path: '/model-info', icon: BookOpen },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-white border-r border-slate-200/80 flex flex-col shrink-0 min-h-[calc(100vh-4rem)] shadow-xs">
      <div className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
        Platform Navigation
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 font-semibold border-l-4 border-l-blue-600 shadow-xs'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-blue-600'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-medium ${
                  item.badgeAccent
                    ? 'bg-amber-100 text-amber-800 border border-amber-200'
                    : 'bg-blue-100/70 text-blue-700 border border-blue-200/60'
                }`}>
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-100 text-[11px] text-slate-500 space-y-1">
        <p className="font-semibold text-slate-700">PolitiTrade LK v1.0</p>
        <p>Colombo Stock Exchange Analytics</p>
        <p className="text-slate-400">Strict Non-Lookahead Design</p>
      </div>
    </aside>
  );
};
