import { NavLink } from 'react-router-dom';
import { Badge } from '@/components/ui/Badge';
import { Award, BarChart3, GitCompare, HelpCircle, Trophy } from 'lucide-react';

export interface ModelLabNavProps {
  totalModels?: number;
  activeModelId?: string;
}

export function ModelLabNav({ totalModels = 277, activeModelId }: ModelLabNavProps) {
  const detailPath = activeModelId ? `/models/${activeModelId}` : '/models/catboost_reg_c_h5';

  const navItems = [
    {
      to: '/models',
      label: 'Leaderboard',
      icon: BarChart3,
      badge: `${totalModels} Models`,
      end: true,
    },
    {
      to: detailPath,
      label: 'Model Diagnostics',
      icon: HelpCircle,
      badge: 'Diagnostics',
      end: false,
    },
    {
      to: '/models/compare',
      label: 'Model Compare',
      icon: GitCompare,
      badge: 'Up to 4',
      end: true,
    },
    {
      to: '/models/statistics',
      label: 'DM Tests & Ablations',
      icon: Award,
      badge: 'Diebold-Mariano',
      end: true,
    },
    {
      to: '/models/final',
      label: 'Champion Model Card',
      icon: Trophy,
      badge: 'Frozen Final',
      end: true,
    },
  ];

  return (
    <div className="border-b border-border">
      <nav className="-mb-px flex flex-wrap gap-2 sm:gap-4" aria-label="Model Lab Sections">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-semibold transition-all ${
                  isActive
                    ? 'border-primary text-primary'
                    : 'text-muted-foreground hover:text-foreground border-transparent hover:border-border'
                }`
              }
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
              <Badge variant="secondary" className="font-mono text-[10px]">
                {item.badge}
              </Badge>
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
}
