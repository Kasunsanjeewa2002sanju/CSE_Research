import { Link } from 'react-router-dom';
import { Newspaper, Clock, Tag, ArrowRight } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { useNewsItemsQuery } from '@/features/news/hooks/useNewsData';

export function RecentNewsPreview() {
  const { data, isLoading, isError } = useNewsItemsQuery(1, 4);

  const articles = data?.items || [];

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Newspaper className="h-5 w-5 text-accent" aria-hidden="true" />
          <h2 className="font-heading text-xl font-bold text-text-primary">
            Recent News & Semantic Sentiment
          </h2>
        </div>
        <Link
          to="/news"
          className="flex items-center gap-1 text-xs font-semibold text-accent hover:underline"
        >
          <span>View All Live Feeds</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="space-y-2 p-4">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-5 w-full" />
              <Skeleton className="h-3 w-32" />
            </Card>
          ))}
        </div>
      ) : isError || articles.length === 0 ? (
        <Card className="p-6">
          <EmptyState
            title="Live News Ingestion Pipeline Scheduled"
            description="Recent news articles are fed continuously by Stage 12 news pipeline (GAP-009). When the live polling daemon is active, incoming Sri Lankan political headlines and market impact scores will appear here."
            gapId="GAP-009"
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {articles.map((item) => (
            <Card
              key={item.id}
              className="flex flex-col justify-between p-4 transition-all hover:shadow-card"
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <Badge variant="navy" size="sm" className="font-mono text-[10px]">
                    {item.source}
                  </Badge>
                  <div className="flex items-center gap-1 font-mono text-[11px] text-text-muted">
                    <Clock className="h-3 w-3" />
                    <span>{item.published_at.substring(0, 10)}</span>
                  </div>
                </div>

                <h3 className="mt-2.5 line-clamp-2 font-heading text-sm font-semibold text-text-primary">
                  {item.title}
                </h3>
                {item.tags && item.tags.length > 0 && (
                  <p className="mt-1 line-clamp-1 text-xs text-text-muted">
                    {item.tags.join(', ')}
                  </p>
                )}
              </div>

              <div className="border-border/50 mt-3 flex items-center justify-between border-t pt-2.5">
                <div className="flex items-center gap-1.5 font-mono text-[11px] text-text-muted">
                  <Tag className="h-3 w-3 text-accent" />
                  <span>{item.category || 'General Politics'}</span>
                </div>
                {item.sentiment_score !== undefined && (
                  <Badge
                    variant={
                      item.sentiment_score > 0
                        ? 'success'
                        : item.sentiment_score < 0
                          ? 'danger'
                          : 'outline'
                    }
                    size="sm"
                    className="font-mono text-[10px]"
                  >
                    Sentiment: {item.sentiment_score > 0 ? '+' : ''}
                    {item.sentiment_score.toFixed(2)}
                  </Badge>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}
