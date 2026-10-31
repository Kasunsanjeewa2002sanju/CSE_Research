import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import type { ProtocolRule } from '../types';

export interface ProtocolRuleCardProps {
  rule: ProtocolRule;
}

export function ProtocolRuleCard({ rule }: ProtocolRuleCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <Badge variant="outline">{rule.category}</Badge>
          <span className="text-muted-foreground font-mono text-xs">{rule.id}</span>
        </div>
        <CardTitle className="mt-2 text-base">{rule.name}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-xs">
        <p className="text-muted-foreground leading-relaxed">{rule.description}</p>
        <div className="border-border/40 text-primary border-t pt-2 font-mono text-[11px]">
          Enforcement: {rule.enforcement}
        </div>
      </CardContent>
    </Card>
  );
}
