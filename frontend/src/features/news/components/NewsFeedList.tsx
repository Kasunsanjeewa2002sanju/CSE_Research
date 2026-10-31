import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ExternalLink } from 'lucide-react';
import { formatDate, formatPercent } from '@/utils/formatters';
import type { NewsArticle } from '../types';

export interface NewsFeedListProps {
  articles: NewsArticle[];
}

export function NewsFeedList({ articles }: NewsFeedListProps) {
  if (articles.length === 0) {
    return (
      <div className="text-muted-foreground p-8 text-center text-sm">
        No live news articles received from monitored feeds.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {articles.map((article) => (
        <Card key={article.id} className="hover:border-primary/50 transition-colors">
          <CardContent className="flex flex-col justify-between gap-3 p-4 text-xs sm:flex-row sm:items-center">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Badge variant="outline">{article.source}</Badge>
                {article.category && (
                  <span className="text-muted-foreground font-mono">[{article.category}]</span>
                )}
                <span className="text-muted-foreground font-mono">
                  {formatDate(article.published_at)}
                </span>
              </div>
              <h4 className="text-foreground font-heading text-sm font-medium">
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-primary flex items-center gap-1.5 transition-colors"
                >
                  {article.title}
                  <ExternalLink className="text-muted-foreground h-3 w-3 shrink-0" />
                </a>
              </h4>
            </div>

            {article.sentiment_score !== undefined && (
              <div className="shrink-0">
                <Badge
                  variant={
                    article.sentiment_score > 0
                      ? 'market-up'
                      : article.sentiment_score < 0
                        ? 'market-down'
                        : 'market-neutral'
                  }
                >
                  Score: {formatPercent(article.sentiment_score, 1, true)}
                </Badge>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
