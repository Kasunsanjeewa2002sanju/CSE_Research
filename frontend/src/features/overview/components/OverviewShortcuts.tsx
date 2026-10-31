import { Link } from 'react-router-dom';
import { Calendar, Activity, Cpu, Newspaper, ArrowRight } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

export function OverviewShortcuts() {
  const shortcuts = [
    {
      to: '/events',
      title: 'Political Events Catalog',
      description:
        'Explore 24 Sri Lankan elections across 146 distinct stages with voter turnout, margins, and calendar mappings.',
      icon: <Calendar className="h-5 w-5 text-accent" />,
      badge: '24 Events',
    },
    {
      to: '/event-study',
      title: 'Event Study Analysis',
      description:
        'Cumulative Average Abnormal Returns (CAAR) across 9 event windows evaluated with 10,000 placebo draws.',
      icon: <Activity className="text-blue-primary h-5 w-5" />,
      badge: '10,000 Permutations',
    },
    {
      to: '/model-lab',
      title: 'Model Lab & Comparison',
      description:
        'Walk-forward leaderboard comparing 245 model configurations with Diebold-Mariano tests and ablation studies.',
      icon: <Cpu className="h-5 w-5 text-accent" />,
      badge: '5 Phases (P1–P5)',
    },
    {
      to: '/news',
      title: 'Live News Ingestion',
      description:
        'Continuous feed monitoring across 8 Sri Lankan news sources with semantic classification and market impact scoring.',
      icon: <Newspaper className="text-blue-primary h-5 w-5" />,
      badge: '8 Feeds',
    },
  ];

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-heading text-xl font-bold text-text-primary">Research Modules</h2>
          <p className="text-xs text-text-muted">
            Direct access to econometric datasets, statistical models, and live news monitoring.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {shortcuts.map((sc) => (
          <Link
            key={sc.to}
            to={sc.to}
            className="group block rounded-card focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <Card className="group-hover:border-accent/40 flex h-full flex-col justify-between p-5 transition-all duration-150 group-hover:-translate-y-0.5 group-hover:shadow-card">
              <div>
                <div className="flex items-center justify-between">
                  <div className="group-hover:bg-accent/10 flex h-10 w-10 items-center justify-center rounded-button bg-surface-subtle">
                    {sc.icon}
                  </div>
                  <Badge variant="outline" size="sm" className="font-mono text-[11px]">
                    {sc.badge}
                  </Badge>
                </div>

                <h3 className="group-hover:text-blue-primary mt-4 font-heading text-base font-bold text-text-primary dark:group-hover:text-accent">
                  {sc.title}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-text-muted">{sc.description}</p>
              </div>

              <div className="mt-4 flex items-center gap-1 font-mono text-xs font-semibold text-accent group-hover:underline">
                <span>Open module</span>
                <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </section>
  );
}
