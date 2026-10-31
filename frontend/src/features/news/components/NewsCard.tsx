import { Link } from 'react-router-dom';
import {
  ExternalLink,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Minus,
  Landmark,
  Scale,
  ShieldAlert,
  AlertTriangle,
  Briefcase,
  Vote,
  Newspaper,
  Layers,
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { formatDateTimeColombo } from '@/utils/formatters';
import type { NewsItem } from '../types';

export interface NewsCardProps {
  item: NewsItem;
  onSelect: (item: NewsItem) => void;
}

function getCategoryIcon(cat: string) {
  const c = cat.toLowerCase();
  if (c.includes('election') || c.includes('vote') || c.includes('nomination') || c.includes('polling')) {
    return Vote;
  }
  if (c.includes('arrest') || c.includes('imprison') || c.includes('security')) {
    return ShieldAlert;
  }
  if (c.includes('court') || c.includes('legal') || c.includes('justice') || c.includes('constitution')) {
    return Scale;
  }
  if (c.includes('economic') || c.includes('market') || c.includes('aspi') || c.includes('inflation')) {
    return TrendingUp;
  }
  if (c.includes('trade') || c.includes('tax') || c.includes('finance') || c.includes('business')) {
    return Briefcase;
  }
  if (c.includes('crisis') || c.includes('emergency') || c.includes('protest')) {
    return AlertTriangle;
  }
  if (c.includes('political') || c.includes('parliament') || c.includes('cabinet') || c.includes('government')) {
    return Landmark;
  }
  return Newspaper;
}

export function NewsCard({ item, onSelect }: NewsCardProps) {
  const IconComponent = getCategoryIcon(item.category || '');
  const direction = (item.direction || 'neutral').toLowerCase();
  const confidencePct = Math.round((item.confidence ?? 0.75) * 100);
  const clusterCount = item.duplicate_cluster?.length ?? 0;

  return (
    <article
      className="group flex flex-col justify-between rounded-card border border-border bg-surface-white p-5 shadow-card transition-all duration-200 hover:-translate-y-0.5 hover:border-blue-cobalt/40 hover:shadow-card-hover"
      aria-labelledby={`news-title-${item.id}`}
    >
      <div>
        {/* Top Media Bar: Thumbnail if API provides image URL; otherwise category icon */}
        <div className="mb-4 flex items-center justify-between gap-3">
          {item.image_url ? (
            <div className="relative h-28 w-full overflow-hidden rounded-md border border-border bg-surface-subtle">
              <img
                src={item.image_url}
                alt={item.title}
                className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                loading="lazy"
              />
            </div>
          ) : (
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border border-border bg-blue-ice text-blue-cobalt group-hover:border-blue-soft group-hover:bg-blue-soft/30">
              <IconComponent className="h-6 w-6" aria-hidden="true" />
            </div>
          )}

          <div className="flex flex-wrap items-center gap-1.5 text-right">
            {clusterCount > 0 && (
              <Badge
                variant="neutral"
                size="sm"
                className="flex items-center gap-1 font-mono text-[11px]"
                title={`${clusterCount} duplicate / syndicated articles clustered`}
              >
                <Layers className="h-3 w-3 text-text-muted" />
                <span>+{clusterCount}</span>
              </Badge>
            )}
            <Badge
              variant={item.is_relevant ? 'primary' : 'neutral'}
              size="sm"
              className="font-mono text-[11px]"
            >
              {item.is_relevant ? 'Macro Relevant' : 'Not Relevant'}
            </Badge>
          </div>
        </div>

        {/* Source & Colombo Publication Timestamp */}
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-xs text-text-muted">
          <span className="font-heading font-semibold text-blue-navy">{item.source}</span>
          <time dateTime={item.published_at} className="font-mono text-[11px] text-text-muted">
            {formatDateTimeColombo(item.published_at)}
          </time>
        </div>

        {/* Headline */}
        <h3
          id={`news-title-${item.id}`}
          onClick={() => onSelect(item)}
          className="mb-3 cursor-pointer font-heading text-base font-bold leading-snug text-text-primary transition-colors hover:text-blue-cobalt line-clamp-2"
          title="Click to view detailed classification & duplicate cluster"
        >
          {item.headline || item.title}
        </h3>

        {/* Classification Chips Row: Category, Stage, Expected Direction, Confidence */}
        <div className="mb-4 flex flex-wrap items-center gap-1.5">
          {/* Category Chip */}
          <span className="inline-flex items-center rounded border border-border/80 bg-surface-subtle px-2 py-0.5 font-mono text-[11px] font-medium text-text-primary uppercase tracking-wider">
            {(item.category || 'general').replace(/_/g, ' ')}
          </span>

          {/* Stage Chip */}
          {item.stage && item.stage !== 'none' && (
            <span className="inline-flex items-center rounded border border-blue-soft bg-blue-ice px-2 py-0.5 font-mono text-[11px] font-medium text-blue-cobalt uppercase tracking-wider">
              {item.stage.replace(/_/g, ' ')}
            </span>
          )}

          {/* Expected Direction Chip */}
          <Badge
            variant={
              direction === 'positive' ? 'market-up' : direction === 'negative' ? 'market-down' : 'neutral'
            }
            size="sm"
            className="flex items-center gap-1 font-mono text-[11px] font-semibold"
          >
            {direction === 'positive' ? (
              <TrendingUp className="h-3 w-3 text-data-up" aria-hidden="true" />
            ) : direction === 'negative' ? (
              <TrendingDown className="h-3 w-3 text-data-down" aria-hidden="true" />
            ) : (
              <Minus className="h-3 w-3 text-text-muted" aria-hidden="true" />
            )}
            <span className="capitalize">{direction}</span>
          </Badge>

          {/* Classifier Confidence */}
          <span
            className="inline-flex items-center rounded border border-border px-1.5 py-0.5 font-mono text-[10px] text-text-muted"
            title={`FinBERT / Classifier Probability: ${(item.confidence ?? 0.75).toFixed(2)}`}
          >
            Conf: <strong className="ml-1 text-text-primary">{confidencePct}%</strong>
          </span>
        </div>
      </div>

      {/* Action Buttons Row */}
      <div className="mt-2 flex items-center justify-between gap-2 border-t border-border/60 pt-3">
        {/* Read article (external link, noopener) */}
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 rounded-button border border-border bg-surface-white px-2.5 py-1.5 text-xs font-semibold text-text-primary shadow-soft transition-all hover:border-blue-cobalt/40 hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-cobalt"
          title="Open original news story in new tab"
        >
          <span>Read article</span>
          <ExternalLink className="h-3.5 w-3.5 text-text-muted" aria-hidden="true" />
        </a>

        {/* Deep link to Predictor */}
        <Link
          to={`/predictor?news=${encodeURIComponent(item.id)}`}
          className="inline-flex items-center gap-1.5 rounded-button bg-accent px-2.5 py-1.5 text-xs font-bold text-accent-foreground shadow-soft transition-all hover:bg-accent-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          title="Simulate conditional market impact in the Scenario Predictor"
        >
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
          <span>Predict impact</span>
        </Link>
      </div>
    </article>
  );
}
export default NewsCard;
