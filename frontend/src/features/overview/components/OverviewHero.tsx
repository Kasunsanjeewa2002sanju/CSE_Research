import { useNavigate } from 'react-router-dom';
import { Sparkles, Calendar, ArrowRight, ShieldAlert } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { useMeta } from '@/context/MetaContext';

export function OverviewHero() {
  const navigate = useNavigate();
  const { getDisclaimer, asOfDate } = useMeta();
  const endYear = asOfDate ? asOfDate.substring(0, 4) : '2026';

  const causationDisclaimer =
    getDisclaimer('causation') ||
    'Statistical association evaluated over 30+ years does not imply direct causation.';

  return (
    <section className="via-blue-ice/40 relative overflow-hidden border-b border-border bg-gradient-to-br from-surface-white to-surface-card px-4 py-10 sm:px-6 lg:px-8">
      {/* Decorative accent element */}
      <div
        className="bg-accent/10 pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full blur-3xl"
        aria-hidden="true"
      />
      <div
        className="bg-blue-vibrant/5 pointer-events-none absolute -left-20 bottom-0 h-48 w-48 rounded-full blur-2xl"
        aria-hidden="true"
      />

      <div className="relative mx-auto max-w-7xl">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-3xl space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="navy" size="sm">
                Academic Research
              </Badge>
              <Badge variant="outline" size="sm" className="font-mono text-xs">
                SLIIT 2026
              </Badge>
              <span className="flex items-center gap-1 font-mono text-[11px] text-text-muted">
                <ShieldAlert className="text-warning h-3 w-3" aria-hidden="true" />
                <span>{causationDisclaimer}</span>
              </span>
            </div>

            <h1 className="font-heading text-3xl font-extrabold tracking-tight text-text-primary sm:text-4xl lg:text-5xl">
              Colombo Stock Exchange ASPI & Political Event Study
            </h1>

            <p className="text-base text-text-muted sm:text-lg">
              Empirical quantitative platform analyzing Sri Lankan elections, constitutional
              milestones, and macroeconomic news against ASPI price movements and returns
              (1994–{endYear}).
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="primary"
              size="lg"
              onClick={() => navigate('/scenario')}
              leftIcon={<Sparkles className="h-4 w-4" />}
              rightIcon={<ArrowRight className="h-4 w-4" />}
            >
              Analyse news impact
            </Button>

            <Button
              variant="outline"
              size="lg"
              onClick={() => navigate('/events')}
              leftIcon={<Calendar className="h-4 w-4" />}
            >
              Explore election events
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
