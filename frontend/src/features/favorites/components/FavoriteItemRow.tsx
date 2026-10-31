import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Link } from 'react-router-dom';
import { Bookmark, ExternalLink } from 'lucide-react';
import { formatDate } from '@/utils/formatters';
import type { FavoriteItem } from '../types';

export interface FavoriteItemRowProps {
  item: FavoriteItem;
}

export function FavoriteItemRow({ item }: FavoriteItemRowProps) {
  return (
    <Card className="hover:border-primary/40 transition-colors">
      <CardContent className="flex items-center justify-between gap-3 p-4 text-xs">
        <div className="flex items-center gap-3">
          <Bookmark className="text-primary h-4 w-4 shrink-0" aria-hidden="true" />
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">{item.item_type}</Badge>
              <span className="text-foreground font-semibold">{item.title}</span>
            </div>
            <div className="text-muted-foreground mt-0.5 font-mono text-[11px]">
              Saved on: {formatDate(item.saved_at)}
            </div>
          </div>
        </div>

        <Link
          to={item.path}
          className="text-primary inline-flex items-center gap-1 font-mono hover:underline"
        >
          <span>Open View</span>
          <ExternalLink className="h-3 w-3" />
        </Link>
      </CardContent>
    </Card>
  );
}
