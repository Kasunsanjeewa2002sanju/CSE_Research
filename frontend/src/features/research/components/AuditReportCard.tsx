import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { CheckCircle2, XCircle } from 'lucide-react';
import type { AuditProof } from '../types';

export interface AuditReportCardProps {
  proof: AuditProof;
}

export function AuditReportCard({ proof }: AuditReportCardProps) {
  const isPass = proof.verdict === 'PASS';

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <Badge variant={isPass ? 'market-up' : 'market-down'} className="flex items-center gap-1">
            {isPass ? (
              <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
            ) : (
              <XCircle className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            <span>{proof.verdict}</span>
          </Badge>
          <span className="text-muted-foreground font-mono text-xs">{proof.dimension}</span>
        </div>
        <CardTitle className="mt-2 text-base">{proof.dimension}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-xs">
        <p className="text-muted-foreground leading-relaxed">{proof.details}</p>
        <div className="border-border/40 text-foreground bg-muted/40 rounded border-t p-2 pt-2 font-mono text-[11px]">
          Proof: {proof.evidence}
        </div>
      </CardContent>
    </Card>
  );
}
