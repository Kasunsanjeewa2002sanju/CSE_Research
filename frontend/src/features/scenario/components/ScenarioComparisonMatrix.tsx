import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Columns } from 'lucide-react';
import type { ScenarioSubmitResponse } from '../types';

export interface ScenarioComparisonMatrixProps {
  result: ScenarioSubmitResponse;
}

export function ScenarioComparisonMatrix({ result }: ScenarioComparisonMatrixProps) {
  const { comparison_matrix } = result;
  const { columns = [], rows = [] } = comparison_matrix || {};

  return (
    <Card className="border-border bg-surface-white shadow-soft">
      <CardHeader className="flex flex-row items-center justify-between border-b border-border/60 pb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-surface-subtle text-text-secondary">
            <Columns className="h-4 w-4" />
          </div>
          <div>
            <CardTitle className="text-base font-semibold text-text-primary">
              Econometric Counterfactual Comparison Matrix
            </CardTitle>
            <p className="text-xs text-text-muted">
              Direct dimensional comparison across Baseline, Scenario TRUE, Scenario FALSE, and Net Impact
            </p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-3">
        <div className="overflow-x-auto font-mono text-xs">
          <table className="w-full border-collapse text-left" aria-label="Scenario Comparison Matrix">
            <thead>
              <tr className="border-b border-border bg-surface-subtle/80 text-[11px] font-semibold text-text-secondary">
                {columns.map((col) => (
                  <th key={col.key} className="p-2.5 font-heading">
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {rows.map((row, idx) => {
                const isPositiveDiff = row.net_diff.startsWith('+');
                const isNegativeDiff = row.net_diff.startsWith('-');

                return (
                  <tr
                    key={row.metric || idx}
                    className="transition-colors hover:bg-surface-subtle/40"
                  >
                    <td className="p-2.5 font-sans font-semibold text-text-primary">
                      {row.metric}
                    </td>
                    <td className="p-2.5 text-text-muted">
                      {row.current}
                    </td>
                    <td className="p-2.5 font-semibold text-blue-navy">
                      {row.true_val}
                    </td>
                    <td className="p-2.5 text-text-secondary">
                      {row.false_val}
                    </td>
                    <td
                      className={`p-2.5 font-bold ${
                        isPositiveDiff
                          ? 'text-green-emerald'
                          : isNegativeDiff
                          ? 'text-red-coral'
                          : 'text-text-primary'
                      }`}
                    >
                      {row.net_diff}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
