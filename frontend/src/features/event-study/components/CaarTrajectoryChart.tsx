import { useMemo, useState } from 'react';
import { EChart } from '@/components/charts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { buildCaarTrajectoryOption, buildAbnormalReturnBarsOption } from '../utils/chart-options';
import type { EventStudyCaarResponse, TrajectoryDisplayMode } from '../types';

export interface CaarTrajectoryChartProps {
  caarData?: EventStudyCaarResponse;
  displayMode?: TrajectoryDisplayMode;
  isLoading?: boolean;
}

export function CaarTrajectoryChart({
  caarData,
  displayMode = 'both',
  isLoading,
}: CaarTrajectoryChartProps) {
  const [showTableAlt, setShowTableAlt] = useState(false);

  const trajectoryOption = useMemo(() => {
    if (!caarData?.data) return {};
    return buildCaarTrajectoryOption(caarData.data, caarData.individual_events, displayMode);
  }, [caarData, displayMode]);

  const arBarsOption = useMemo(() => {
    if (!caarData?.data) return {};
    return buildAbnormalReturnBarsOption(caarData.data);
  }, [caarData]);

  if (isLoading || !caarData) {
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
              Cumulative Average Abnormal Return (CAAR) Path
            </CardTitle>
            <Badge variant="outline" className="font-mono text-xs">
              Window {caarData.window_days}
            </Badge>
          </div>
          <p className="text-muted-foreground mt-0.5 text-xs">
            Mean trajectory highlighted against 95% non-event permutation band. Light curves show
            individual events (hover to inspect).
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setShowTableAlt((prev) => !prev)}
            className="text-primary text-xs font-medium hover:underline"
            aria-expanded={showTableAlt}
          >
            {showTableAlt ? 'Show Chart View' : 'Accessible Data Table'}
          </button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 p-4">
        {showTableAlt ? (
          <div className="max-h-96 overflow-x-auto rounded-card border border-border">
            <table className="w-full text-left font-mono text-xs">
              <thead className="border-b border-border bg-surface-subtle text-[11px] uppercase text-text-muted">
                <tr>
                  <th className="px-3 py-2 font-semibold">Trading Day (t)</th>
                  <th className="px-3 py-2 text-right font-semibold">Mean CAAR (%)</th>
                  <th className="px-3 py-2 text-right font-semibold">95% CI Lower (%)</th>
                  <th className="px-3 py-2 text-right font-semibold">95% CI Upper (%)</th>
                  <th className="px-3 py-2 text-right font-semibold">Daily AR (%)</th>
                  <th className="px-3 py-2 text-right font-semibold">Sample Size</th>
                </tr>
              </thead>
              <tbody className="divide-border/60 divide-y bg-surface-white">
                {caarData.data.map((pt) => (
                  <tr key={pt.day} className="hover:bg-blue-ice/30 transition-colors">
                    <td className="px-3 py-2 font-medium">
                      {pt.day === 0 ? 't=0 (Event Day)' : `t=${pt.day > 0 ? `+${pt.day}` : pt.day}`}
                    </td>
                    <td className="px-3 py-2 text-right font-bold text-text-primary">
                      {pt.caar > 0 ? `+${pt.caar}` : pt.caar}%
                    </td>
                    <td className="px-3 py-2 text-right text-text-muted">{pt.ci_lower_95}%</td>
                    <td className="px-3 py-2 text-right text-text-muted">{pt.ci_upper_95}%</td>
                    <td className="px-3 py-2 text-right">
                      {pt.ar !== undefined ? (pt.ar > 0 ? `+${pt.ar}%` : `${pt.ar}%`) : '—'}
                    </td>
                    <td className="px-3 py-2 text-right">{pt.sample_size}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="space-y-2">
            {/* 1. Main CAAR Curve */}
            <div className="w-full">
              <EChart option={trajectoryOption} height={290} />
            </div>

            {/* 2. Daily Abnormal Return (AR) Bars */}
            <div className="border-border/40 border-t pt-2">
              <span className="text-muted-foreground mb-1 block text-[11px] font-semibold uppercase tracking-wider">
                Daily Abnormal Return (AR<sub>t</sub>) Impulse
              </span>
              <div className="w-full">
                <EChart option={arBarsOption} height={130} />
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
