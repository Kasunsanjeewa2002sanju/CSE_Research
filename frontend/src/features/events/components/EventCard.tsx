import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatDate, formatPercent } from '@/utils/formatters';
import type { PoliticalEvent } from '../types';

export interface EventCardProps {
  event: PoliticalEvent;
}

export function EventCard({ event }: EventCardProps) {
  const winner = event.winner_party || event.outcome_party;
  const margin = event.margin_pct ?? event.margin;
  const turnout = event.turnout_pct ?? event.turnout;

  return (
    <Card className="hover:border-primary/50 transition-colors">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <Badge variant="outline">{event.category}</Badge>
          <span className="text-muted-foreground font-mono text-xs">{formatDate(event.date)}</span>
        </div>
        <CardTitle className="mt-2 text-base">{event.name}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-xs">
        {winner && (
          <div className="text-muted-foreground flex items-center justify-between">
            <span>Winning Party / Coalition:</span>
            <span className="text-foreground font-semibold">{winner}</span>
          </div>
        )}
        {margin !== undefined && (
          <div className="text-muted-foreground flex items-center justify-between">
            <span>Victory Margin:</span>
            <span className="text-foreground font-mono">{formatPercent(margin, 2)}</span>
          </div>
        )}
        {turnout !== undefined && (
          <div className="text-muted-foreground flex items-center justify-between">
            <span>Voter Turnout:</span>
            <span className="text-foreground font-mono">{formatPercent(turnout, 2)}</span>
          </div>
        )}
        {event.description && (
          <p className="text-muted-foreground border-border/40 border-t pt-1 leading-relaxed">
            {event.description}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
