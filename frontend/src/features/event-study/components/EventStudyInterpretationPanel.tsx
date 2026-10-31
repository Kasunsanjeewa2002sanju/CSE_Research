import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { AlertCircle, ShieldAlert, BookOpen } from 'lucide-react';
import type { EventStudySummaryResponse } from '../types';

export interface EventStudyInterpretationPanelProps {
  summary?: EventStudySummaryResponse;
  isLoading?: boolean;
}

export function EventStudyInterpretationPanel({
  summary,
  isLoading,
}: EventStudyInterpretationPanelProps) {
  if (isLoading || !summary) {
    return (
      <Card className="h-64 animate-pulse">
        <CardContent className="h-full" />
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* 1. Methodology & Formal Specification Card */}
      <Card className="border-border/80 shadow-sm">
        <CardHeader className="border-border/40 flex flex-row items-center justify-between gap-2 border-b pb-3">
          <div className="flex items-center gap-2">
            <BookOpen className="text-primary h-4 w-4" />
            <CardTitle className="text-base font-semibold">
              Econometric Methodology &amp; Estimation Framework
            </CardTitle>
          </div>
          <Badge variant="outline" className="text-xs">
            Campbell, Lo &amp; MacKinlay (1997)
          </Badge>
        </CardHeader>
        <CardContent className="text-muted-foreground space-y-3 p-4 text-xs leading-relaxed">
          <p className="text-foreground font-medium">{summary.methodology}</p>
          <div className="border-border/60 bg-muted/30 space-y-1 rounded-lg border p-3 font-mono text-[11px]">
            <div className="text-foreground font-semibold">Formulas Implemented:</div>
            <div>
              AR<sub>i,t</sub> = R<sub>i,t</sub> - E[R<sub>i,t</sub> | &Omega;<sub>t-1</sub>]
            </div>
            <div>
              CAR<sub>i</sub>(t<sub>1</sub>, t<sub>2</sub>) = &sum;<sub>t=t1</sub>
              <sup>t2</sup> AR<sub>i,t</sub>
            </div>
            <div>
              CAAR(t<sub>1</sub>, t<sub>2</sub>) = (1 / N) &sum;<sub>i=1</sub>
              <sup>N</sup> CAR<sub>i</sub>(t<sub>1</sub>, t<sub>2</sub>)
            </div>
            <div>
              t<sub>BW</sub> = CAAR / (&sigma;<sub>AR</sub> &radic;T<sub>w</sub>) &mdash;
              Brown-Warner (1985) adjustment
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 2. Mandatory Caveats & Empirical Warnings */}
      <Card className="border-border/80 shadow-sm">
        <CardHeader className="border-border/40 flex flex-row items-center gap-2 border-b pb-3">
          <ShieldAlert className="h-4 w-4 text-amber-600 dark:text-amber-400" />
          <CardTitle className="text-base font-semibold">
            Empirical Caveats &amp; Statistical Limitations
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2.5 p-4">
          <div className="space-y-2">
            {summary.caveats.map((cav, idx) => (
              <div
                key={idx}
                className="text-muted-foreground flex items-start gap-2.5 text-xs leading-relaxed"
              >
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
                <span>{cav}</span>
              </div>
            ))}
          </div>

          <div className="border-border/40 bg-surface-subtle/50 text-muted-foreground mt-3 rounded-lg border p-2.5 text-[11px] italic">
            <strong>Platform Disclaimer:</strong> {summary.disclaimer}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
