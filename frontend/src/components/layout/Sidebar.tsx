import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  LineChart,
  CalendarDays,
  Target,
  FlaskConical,
  Cpu,
  Newspaper,
  Compass,
  FileText,
  Bookmark,
  MessageSquare,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/data-explorer', label: 'Data Explorer', icon: LineChart },
  { to: '/events', label: 'Political Events', icon: CalendarDays },
  { to: '/event-study', label: 'Event Study', icon: Target },
  { to: '/model-lab', label: 'Model Lab', icon: Cpu },
  { to: '/scenario', label: 'Scenario Simulator', icon: Compass },
  { to: '/news', label: 'News Intelligence', icon: Newspaper },
  { to: '/methodology', label: 'Methodology', icon: FlaskConical },
  { to: '/research', label: 'Research & Audit', icon: FileText },
  { to: '/favorites', label: 'Saved Views', icon: Bookmark },
  { to: '/feedback', label: 'Reviewer Feedback', icon: MessageSquare },
];

export function Sidebar() {
  return (
    <aside className="bg-card/40 flex min-h-[calc(100vh-61px)] w-64 shrink-0 flex-col border-r border-border">
      <div className="flex-1 p-4">
        <div className="text-muted-foreground mb-2 px-3 font-mono text-[11px] uppercase tracking-wider">
          Research Modules
        </div>
        <nav className="space-y-1" aria-label="Main Navigation">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'
                  )
                }
              >
                <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      <div className="border-border/60 text-muted-foreground space-y-1 border-t p-4 font-mono text-[11px]">
        <div>Platform Rules: FR1–FR10</div>
        <div>Strict Zero-Leakage Architecture</div>
      </div>
    </aside>
  );
}
