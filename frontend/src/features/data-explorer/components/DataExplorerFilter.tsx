import { Card, CardContent } from '@/components/ui/Card';
import { Filter } from 'lucide-react';

export interface DataExplorerFilterProps {
  totalRecords?: number;
  startDate?: string;
  endDate?: string;
}

export function DataExplorerFilter({ totalRecords, startDate, endDate }: DataExplorerFilterProps) {
  return (
    <Card className="bg-card/60">
      <CardContent className="flex flex-wrap items-center justify-between gap-4 p-4 font-mono text-xs">
        <div className="text-muted-foreground flex items-center gap-2">
          <Filter className="text-primary h-4 w-4" aria-hidden="true" />
          <span>Historical Horizon Coverage</span>
        </div>
        <div className="flex items-center gap-4">
          {totalRecords !== undefined && (
            <span>
              <strong className="text-foreground">Observations:</strong>{' '}
              {totalRecords.toLocaleString()}
            </span>
          )}
          {startDate && endDate && (
            <span>
              <strong className="text-foreground">Span:</strong> {startDate} to {endDate}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
