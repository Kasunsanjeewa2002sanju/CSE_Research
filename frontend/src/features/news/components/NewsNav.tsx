import { NavLink } from 'react-router-dom';
import { Newspaper, Activity, RefreshCw } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { IconButton } from '@/components/ui/IconButton';

export interface NewsNavProps {
  totalArticles?: number;
  activeFeeds?: number;
  totalFeeds?: number;
  refreshIntervalSec?: number;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function NewsNav({
  totalArticles,
  activeFeeds,
  totalFeeds,
  refreshIntervalSec = 300,
  onRefresh,
  isRefreshing = false,
}: NewsNavProps) {
  const navItems = [
    {
      to: '/news',
      label: 'News Intelligence Feed',
      icon: Newspaper,
      badge: totalArticles !== undefined ? `${totalArticles} Articles` : undefined,
      end: true,
    },
    {
      to: '/news/pipeline',
      label: 'Ingestion Pipeline Monitor',
      icon: Activity,
      badge:
        activeFeeds !== undefined && totalFeeds !== undefined
          ? `${activeFeeds}/${totalFeeds} Active Feeds`
          : undefined,
      end: true,
    },
  ];

  return (
    <div className="flex flex-col gap-3 border-b border-border pb-3 sm:flex-row sm:items-center sm:justify-between">
      <nav className="-mb-px flex flex-wrap gap-2 sm:gap-4" aria-label="News Sections">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `group inline-flex items-center gap-2 border-b-2 px-3 py-2.5 font-heading text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                  isActive
                    ? 'border-blue-cobalt text-blue-navy'
                    : 'border-transparent text-text-muted hover:border-border hover:text-text-primary'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    className={`h-4 w-4 transition-colors ${
                      isActive ? 'text-blue-cobalt' : 'text-text-muted group-hover:text-text-primary'
                    }`}
                    aria-hidden="true"
                  />
                  <span>{item.label}</span>
                  {item.badge && (
                    <Badge
                      variant={isActive ? 'primary' : 'neutral'}
                      size="sm"
                      className="ml-1 font-mono text-xs"
                    >
                      {item.badge}
                    </Badge>
                  )}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Auto-refresh indicator from API meta & manual trigger */}
      <div className="flex items-center gap-3 text-xs text-text-muted">
        <div className="flex items-center gap-1.5 font-mono">
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Auto-refresh: {refreshIntervalSec}s (API Meta)</span>
        </div>
        {onRefresh && (
          <IconButton
            variant="ghost"
            size="sm"
            onClick={onRefresh}
            disabled={isRefreshing}
            aria-label="Refresh news feed now"
            title="Refresh now"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin text-blue-cobalt' : ''}`} />
          </IconButton>
        )}
      </div>
    </div>
  );
}
export default NewsNav;
