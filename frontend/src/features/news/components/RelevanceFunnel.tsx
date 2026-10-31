import { ArrowDown, CheckCircle2, Filter, Layers, Sparkles } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import type { RelevanceFunnel as RelevanceFunnelType } from '../types';

export interface RelevanceFunnelProps {
  funnel?: RelevanceFunnelType;
  isLoading?: boolean;
}

const STAGE_ICONS = [
  Filter,      // Fetched
  Layers,      // Deduplicated
  CheckCircle2, // Relevant
  Sparkles,    // Predicted
];

export function RelevanceFunnel({ funnel, isLoading = false }: RelevanceFunnelProps) {
  if (isLoading || !funnel) {
    return (
      <Card className="p-5 shadow-card">
        <div className="h-6 w-48 animate-pulse rounded bg-surface-subtle" />
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 animate-pulse rounded-card bg-surface-subtle" />
          ))}
        </div>
      </Card>
    );
  }

  const { stages, conversion_rate_pct, deduplication_rate_pct } = funnel;

  return (
    <Card className="p-5 shadow-card">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-3">
        <div>
          <h3 className="font-heading text-sm font-bold text-text-primary">
            Pipeline Relevance & Deduplication Funnel
          </h3>
          <p className="text-xs text-text-muted">
            End-to-end multi-stage filtration from raw RSS polling to counterfactual scenario simulation.
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="text-text-muted">Conversion Rate:</span>
            <strong className="text-blue-cobalt">{conversion_rate_pct}%</strong>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-text-muted">Duplicate Filtering:</span>
            <strong className="text-text-primary">{deduplication_rate_pct}%</strong>
          </div>
        </div>
      </div>

      {/* Funnel Steps */}
      <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {stages.map((st, idx) => {
          const Icon = STAGE_ICONS[idx % STAGE_ICONS.length];
          const isFinal = idx === stages.length - 1;

          return (
            <div
              key={st.stage}
              className={`relative flex flex-col justify-between rounded-card border p-4 shadow-soft transition-all ${
                isFinal
                  ? 'border-accent bg-blue-ice/50 text-text-primary'
                  : 'border-border bg-surface-white'
              }`}
            >
              <div>
                <div className="flex items-center justify-between text-xs text-text-muted">
                  <span className="font-mono text-[10px] uppercase font-bold tracking-wider">
                    Step {idx + 1}
                  </span>
                  <Icon
                    className={`h-4 w-4 ${isFinal ? 'text-accent' : 'text-blue-cobalt'}`}
                    aria-hidden="true"
                  />
                </div>

                <h4 className="mt-1 font-heading text-sm font-bold text-text-primary">
                  {st.label}
                </h4>

                <div className="mt-2 flex items-baseline gap-2">
                  <span className="font-mono text-2xl font-extrabold text-text-primary">
                    {st.count.toLocaleString()}
                  </span>
                  <span className="font-mono text-xs font-semibold text-blue-cobalt">
                    ({st.percentage}%)
                  </span>
                </div>

                <p className="mt-2 text-[11px] leading-relaxed text-text-muted">
                  {st.description}
                </p>
              </div>

              {/* Conversion indicator arrow between cards on desktop */}
              {idx < stages.length - 1 && (
                <div className="hidden lg:block absolute -right-2.5 top-1/2 -translate-y-1/2 z-10 rounded-full border border-border bg-surface-white p-0.5 text-text-muted shadow-soft">
                  <ArrowDown className="h-3 w-3 -rotate-90" aria-hidden="true" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
export default RelevanceFunnel;
