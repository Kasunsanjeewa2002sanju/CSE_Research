import { Link } from 'react-router-dom';
import {
  ExternalLink,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Minus,
  Layers,
  Calendar,
  Building2,
  Tag,
  AlertCircle,
} from 'lucide-react';
import { Drawer } from '@/components/ui/Drawer';
import { Badge } from '@/components/ui/Badge';
import { formatDateTimeColombo } from '@/utils/formatters';
import type { NewsItem } from '../types';

export interface NewsDetailDrawerProps {
  item: NewsItem | null;
  onClose: () => void;
}

export function NewsDetailDrawer({ item, onClose }: NewsDetailDrawerProps) {
  if (!item) return null;

  const direction = (item.direction || 'neutral').toLowerCase();
  const confidencePct = Math.round((item.confidence ?? 0.75) * 100);
  const cluster = item.duplicate_cluster || [];
  const entities = item.entities || [];
  const sectors = item.affected_sectors || [];

  return (
    <Drawer
      open={Boolean(item)}
      onClose={onClose}
      title="Article Intelligence & Classification"
      description="Stage 10 classification attributes, duplicate story clusters, and counterfactual scenario preview."
      className="sm:w-[480px] md:w-[540px]"
    >
      <div className="space-y-6">
        {/* Header Metadata Block */}
        <div className="space-y-2 rounded-card border border-border bg-surface-white p-4 shadow-soft">
          <div className="flex items-center justify-between gap-2">
            <span className="font-heading text-xs font-bold uppercase tracking-wider text-blue-cobalt">
              {item.source}
            </span>
            <div className="flex items-center gap-1.5 font-mono text-[11px] text-text-muted">
              <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
              <span>{formatDateTimeColombo(item.published_at)}</span>
            </div>
          </div>

          <h2 className="font-heading text-base font-extrabold leading-snug text-text-primary">
            {item.headline || item.title}
          </h2>

          {item.description && item.description !== item.headline && (
            <p className="text-xs leading-relaxed text-text-muted">{item.description}</p>
          )}

          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-border/60">
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-button border border-border bg-surface-white px-3 py-1.5 text-xs font-semibold text-text-primary shadow-soft hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-cobalt"
            >
              <span>Read original source</span>
              <ExternalLink className="h-3.5 w-3.5 text-text-muted" aria-hidden="true" />
            </a>

            <Link
              to={`/predictor?news=${encodeURIComponent(item.id)}`}
              onClick={onClose}
              className="inline-flex items-center gap-1.5 rounded-button bg-accent px-3 py-1.5 text-xs font-bold text-accent-foreground shadow-soft hover:bg-accent-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Predict impact</span>
            </Link>
          </div>
        </div>

        {/* Section 1: Structured Classification */}
        <div className="space-y-3">
          <h3 className="font-heading text-xs font-bold uppercase tracking-wider text-text-muted">
            Structured Classification
          </h3>
          <div className="grid grid-cols-2 gap-2.5">
            <div className="rounded-card border border-border bg-surface-white p-3">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                Event Category
              </span>
              <p className="mt-0.5 font-heading text-xs font-bold text-text-primary uppercase">
                {(item.category || 'political').replace(/_/g, ' ')}
              </p>
            </div>

            <div className="rounded-card border border-border bg-surface-white p-3">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                Political Stage
              </span>
              <p className="mt-0.5 font-heading text-xs font-bold text-text-primary uppercase">
                {(item.stage || 'none').replace(/_/g, ' ')}
              </p>
            </div>

            <div className="rounded-card border border-border bg-surface-white p-3">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                Expected Direction
              </span>
              <div className="mt-1 flex items-center gap-1.5">
                <Badge
                  variant={
                    direction === 'positive' ? 'market-up' : direction === 'negative' ? 'market-down' : 'neutral'
                  }
                  size="sm"
                  className="font-mono text-xs font-semibold"
                >
                  {direction === 'positive' ? (
                    <TrendingUp className="mr-1 h-3 w-3 text-data-up" />
                  ) : direction === 'negative' ? (
                    <TrendingDown className="mr-1 h-3 w-3 text-data-down" />
                  ) : (
                    <Minus className="mr-1 h-3 w-3 text-text-muted" />
                  )}
                  <span className="capitalize">{direction}</span>
                </Badge>
                {item.sentiment_score !== undefined && (
                  <span className="font-mono text-[11px] text-text-muted">
                    ({item.sentiment_score > 0 ? `+${item.sentiment_score}` : item.sentiment_score})
                  </span>
                )}
              </div>
            </div>

            <div className="rounded-card border border-border bg-surface-white p-3">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                Classifier Confidence
              </span>
              <p className="mt-0.5 font-mono text-xs font-bold text-text-primary">
                {confidencePct}% <span className="font-normal text-text-muted">({item.confidence ?? 0.75})</span>
              </p>
            </div>

            <div className="rounded-card border border-border bg-surface-white p-3">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                Macroeconomic Relevance
              </span>
              <div className="mt-1">
                <Badge variant={item.is_relevant ? 'primary' : 'neutral'} size="sm">
                  {item.is_relevant ? 'Macro Relevant' : 'Not Relevant'}
                </Badge>
              </div>
            </div>

            <div className="rounded-card border border-border bg-surface-white p-3">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                Evidence Strength
              </span>
              <p className="mt-0.5 font-heading text-xs font-semibold capitalize text-text-primary">
                {item.evidence_strength || 'weak'}
              </p>
            </div>
          </div>
        </div>

        {/* Section 2: Reason Text */}
        <div className="space-y-2 rounded-card border border-border bg-surface-white p-4">
          <h3 className="flex items-center gap-1.5 font-heading text-xs font-bold uppercase tracking-wider text-text-muted">
            <AlertCircle className="h-3.5 w-3.5 text-blue-cobalt" />
            <span>Reason & Classification Rationale</span>
          </h3>
          <p className="text-xs leading-relaxed text-text-primary">
            {item.reason || 'Article evaluated by Stage 10 financial NLP taxonomy for Colombo market sentiment.'}
          </p>
        </div>

        {/* Section 3: Entities & Affected Sectors */}
        <div className="space-y-3">
          <h3 className="flex items-center gap-1.5 font-heading text-xs font-bold uppercase tracking-wider text-text-muted">
            <Building2 className="h-3.5 w-3.5 text-text-muted" />
            <span>Entities & Sectors</span>
          </h3>
          <div className="rounded-card border border-border bg-surface-white p-4 space-y-3">
            <div>
              <span className="text-[11px] font-semibold text-text-muted">Extracted Entities:</span>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {entities.length > 0 ? (
                  entities.map((ent, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center rounded border border-border bg-surface-subtle px-2 py-0.5 font-mono text-[11px] text-text-primary"
                    >
                      <Tag className="mr-1 h-3 w-3 text-text-muted" />
                      {ent}
                    </span>
                  ))
                ) : (
                  <span className="text-xs italic text-text-muted">No specific corporate entity detected</span>
                )}
              </div>
            </div>

            {sectors.length > 0 && (
              <div className="border-t border-border/60 pt-2.5">
                <span className="text-[11px] font-semibold text-text-muted">Affected CSE Sectors:</span>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {sectors.map((sec, idx) => (
                    <Badge key={idx} variant="neutral" size="sm" className="font-mono text-[11px]">
                      {sec}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Section 4: Cluster of Duplicate Articles */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="flex items-center gap-1.5 font-heading text-xs font-bold uppercase tracking-wider text-text-muted">
              <Layers className="h-3.5 w-3.5 text-text-muted" />
              <span>Duplicate Story Cluster ({cluster.length})</span>
            </h3>
            <span className="text-[10px] text-text-muted">Fuzzy similarity &gt;0.85</span>
          </div>

          {cluster.length > 0 ? (
            <div className="space-y-2">
              {cluster.map((cItem, i) => (
                <div
                  key={cItem.id || i}
                  className="rounded-card border border-border bg-surface-white p-3 transition-colors hover:border-blue-cobalt/40"
                >
                  <div className="flex items-center justify-between gap-2 text-[10px] text-text-muted">
                    <span className="font-heading font-semibold text-blue-navy">{cItem.source}</span>
                    {cItem.published_at && (
                      <span className="font-mono">{formatDateTimeColombo(cItem.published_at)}</span>
                    )}
                  </div>
                  <p className="mt-1 text-xs font-semibold text-text-primary leading-snug">
                    {cItem.headline}
                  </p>
                  {cItem.url && (
                    <a
                      href={cItem.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-blue-cobalt hover:underline"
                    >
                      <span>Read syndicated source</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-card border border-dashed border-border p-4 text-center text-xs text-text-muted">
              No duplicate or syndicated articles detected across other RSS feeds for this story.
            </div>
          )}
        </div>
      </div>
    </Drawer>
  );
}
export default NewsDetailDrawer;
