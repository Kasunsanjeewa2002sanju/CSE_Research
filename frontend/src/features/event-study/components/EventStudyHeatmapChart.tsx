import { useMemo, useState } from 'react';
import { EChart } from '@/components/charts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { buildHeatmapOption } from '../utils/chart-options';
import type { EventStudyHeatmapResponse } from '../types';

export interface EventStudyHeatmapChartProps {
  heatmapData?: EventStudyHeatmapResponse;
  isLoading?: boolean;
}

export function EventStudyHeatmapChart({ heatmapData, isLoading }: EventStudyHeatmapChartProps) {
  const [showTableAlt, setShowTableAlt] = useState(false);

  const heatmapOption = useMemo(() => {
    if (!heatmapData) return {};
    return buildHeatmapOption(heatmapData);
  }, [heatmapData]);

  if (isLoading || !heatmapData) {
    return (
      <Card className="h-96 animate-pulse">
        <CardContent className="h-full" />
      </Card>
    );
  }

  return (
    <Card className="border-border/80 shadow-sm">
      <CardHeader className="border-border/40 flex flex-row flex-wrap items-center justify-between gap-2 border-b pb-3">
        <div>
          <div className="flex items-center gap-2">
            <CardTitle className="text-base font-semibold">
              Cross-Stage &amp; Multi-Window CAAR Heatmap Matrix
            </CardTitle>
            <Badge variant="outline" className="text-xs">
              {heatmapData.cells.length} Empirical Cells
            </Badge>
          </div>
          <p className="text-muted-foreground mt-0.5 text-xs">
            Average CAR across Election Type &times; Electoral Stage &times; Event Window. Marks
            denote Benjamini-Hochberg FDR corrected significance (q &lt; 0.05).
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowTableAlt((prev) => !prev)}
          className="text-primary text-xs font-medium hover:underline"
          aria-expanded={showTableAlt}
        >
          {showTableAlt ? 'Show Heatmap View' : 'Accessible Matrix Table'}
        </button>
      </CardHeader>

      <CardContent className="p-4">
        {showTableAlt ? (
          <div className="max-h-96 overflow-x-auto rounded-card border border-border">
            <table className="w-full text-left font-mono text-xs">
              <thead className="border-b border-border bg-surface-subtle text-[11px] uppercase text-text-muted">
                <tr>
                  <th className="px-3 py-2 font-semibold">Election Type</th>
                  <th className="px-3 py-2 font-semibold">Stage</th>
                  <th className="px-3 py-2 font-semibold">Window</th>
                  <th className="px-3 py-2 text-right font-semibold">Mean CAAR (%)</th>
                  <th className="px-3 py-2 text-right font-semibold">Sample (n)</th>
                  <th className="px-3 py-2 text-right font-semibold">t-statistic</th>
                  <th className="px-3 py-2 text-right font-semibold">BH FDR p-val</th>
                </tr>
              </thead>
              <tbody className="divide-border/60 divide-y bg-surface-white">
                {heatmapData.cells.map((c, idx) => (
                  <tr key={idx} className="hover:bg-blue-ice/30 transition-colors">
                    <td className="px-3 py-2 font-medium">{c.election_type}</td>
                    <td className="px-3 py-2 capitalize">{c.stage.replace('_', ' ')}</td>
                    <td className="px-3 py-2 font-mono text-xs">{c.window}</td>
                    <td className="px-3 py-2 text-right font-mono font-bold">
                      {c.caar > 0 ? `+${c.caar}` : c.caar}%
                    </td>
                    <td className="px-3 py-2 text-right font-mono">{c.n}</td>
                    <td className="px-3 py-2 text-right font-mono">
                      {c.t_stat?.toFixed(2) ?? '—'}
                    </td>
                    <td className="px-3 py-2 text-right font-mono">
                      {c.t_pval_bh} {c.is_significant ? '(**)' : ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="w-full">
            <EChart option={heatmapOption} height={420} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
