import { useState } from 'react';
import { HelpCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Tooltip } from '@/components/ui/Tooltip';
import { Sparkline } from '@/components/charts/Sparkline';
import type { ScenarioSubmitResponse, ScenarioPanel } from '../types';

export interface ScenarioThreePanelsProps {
  result: ScenarioSubmitResponse;
}

export function ScenarioThreePanels({ result }: ScenarioThreePanelsProps) {
  const [selectedHorizon, setSelectedHorizon] = useState<'1' | '2' | '5' | '10'>('5');

  const { scenarios, meaning_of_false } = result;
  const current = scenarios.CURRENT;
  const truePanel = scenarios.TRUE;
  const falsePanel = scenarios.FALSE;

  // Horizon resolution helper
  const getHorizonValues = (panel: ScenarioPanel) => {
    if (panel.horizons && panel.horizons[selectedHorizon]) {
      const hData = panel.horizons[selectedHorizon];
      return {
        expectedReturnPct: hData.expected_return_pct,
        targetAspi: hData.target_aspi,
        probUp: hData.probability_up,
        interval80: hData.interval_80,
        interval95: hData.interval_95,
        trendDir: hData.trend_direction,
        trendArrow: hData.trend_arrow,
        trendSign: hData.trend_sign,
      };
    }
    return {
      expectedReturnPct: panel.expected_return_pct,
      targetAspi: panel.target_aspi,
      probUp: panel.probability_up,
      interval80: panel.interval_80,
      interval95: panel.interval_95,
      trendDir: panel.trend_direction,
      trendArrow: panel.trend_arrow,
      trendSign: panel.trend_sign,
    };
  };

  const formatReturnPct = (ret: number) => {
    if (ret > 0) return `+${ret.toFixed(2)}%`;
    return `${ret.toFixed(2)}%`;
  };

  const trueVals = getHorizonValues(truePanel);
  const falseVals = getHorizonValues(falsePanel);

  const horizonLabels: Record<string, string> = {
    '1': '1-Day Ahead (t+1)',
    '2': '2-Day Ahead (t+2)',
    '5': '5-Day Weekly (t+5)',
    '10': '10-Day Fortnight (t+10)',
  };

  const renderTrendIcon = (dir: string) => {
    if (dir === 'positive') return <TrendingUp className="h-3.5 w-3.5 text-green-emerald" />;
    if (dir === 'negative') return <TrendingDown className="h-3.5 w-3.5 text-red-coral" />;
    return <Minus className="h-3.5 w-3.5 text-text-muted" />;
  };

  return (
    <div className="space-y-3">
      {/* Horizon Selector Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-2">
        <span className="text-xs font-semibold text-text-primary">
          Projection Horizon Window:
        </span>
        <div className="flex rounded-md border border-border bg-surface-subtle p-0.5 font-mono text-xs">
          {(['1', '2', '5', '10'] as const).map((h) => (
            <button
              key={h}
              type="button"
              onClick={() => setSelectedHorizon(h)}
              className={`rounded px-2.5 py-1 font-medium transition-all ${
                selectedHorizon === h
                  ? 'bg-blue-cobalt text-white shadow-xs'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              h = {h} ({h === '5' ? '1-Week' : h === '1' ? '1-Day' : h === '2' ? '2-Day' : '2-Week'})
            </button>
          ))}
        </div>
      </div>

      {/* The Three Panels Grid */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {/* PANEL 1: Current Baseline */}
        <Card className="border-border bg-surface-white shadow-soft">
          <CardHeader className="border-b border-border/60 pb-2.5">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold text-text-secondary">
                {current.name}
              </CardTitle>
              <Tooltip content="Historical market index level prior to the evaluated scenario event shock.">
                <HelpCircle className="h-3.5 w-3.5 cursor-pointer text-text-muted" />
              </Tooltip>
            </div>
            <p className="text-[11px] text-text-muted">Prevailing as-of baseline</p>
          </CardHeader>
          <CardContent className="space-y-3 pt-3">
            <div>
              <span className="text-[11px] font-medium text-text-muted">Baseline ASPI Level</span>
              <div className="font-mono text-2xl font-bold text-text-primary">
                {current.target_aspi.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 border-y border-border/50 py-2 font-mono text-xs">
              <div>
                <span className="text-[10px] text-text-muted">Expected Return</span>
                <div className="font-semibold text-text-primary">0.00%</div>
              </div>
              <div>
                <span className="text-[10px] text-text-muted">P(Up Move)</span>
                <div className="font-semibold text-text-primary">50.0%</div>
              </div>
            </div>

            <div className="space-y-1 text-xs">
              <div className="flex justify-between font-mono text-[11px]">
                <span className="text-text-muted">80% Interval:</span>
                <span className="text-text-secondary">
                  [{current.interval_80[0].toLocaleString()} - {current.interval_80[1].toLocaleString()}]
                </span>
              </div>
              <div className="flex justify-between font-mono text-[11px]">
                <span className="text-text-muted">95% Interval:</span>
                <span className="text-text-secondary">
                  [{current.interval_95[0].toLocaleString()} - {current.interval_95[1].toLocaleString()}]
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <span className="inline-flex items-center gap-1 rounded bg-surface-subtle px-2 py-0.5 font-mono text-[11px] text-text-muted">
                {renderTrendIcon('neutral')} Flat Anchor
              </span>
              <Sparkline data={current.sparkline} width={80} height={20} color="#718096" />
            </div>
          </CardContent>
        </Card>

        {/* PANEL 2: If the news is TRUE */}
        <Card className="border-blue-soft/80 bg-blue-ice/15 shadow-soft ring-1 ring-blue-soft/30">
          <CardHeader className="border-b border-blue-soft/40 pb-2.5">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold text-blue-navy">
                {truePanel.name}
              </CardTitle>
              <Tooltip content="Counterfactual trajectory assuming the reported political or economic event occurs as announced.">
                <HelpCircle className="h-3.5 w-3.5 cursor-pointer text-blue-cobalt" />
              </Tooltip>
            </div>
            <p className="text-[11px] text-blue-navy/70">{horizonLabels[selectedHorizon]}</p>
          </CardHeader>
          <CardContent className="space-y-3 pt-3">
            <div>
              <span className="text-[11px] font-medium text-text-muted">Projected ASPI Target</span>
              <div className="font-mono text-2xl font-bold text-blue-navy">
                {trueVals.targetAspi.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 border-y border-blue-soft/30 py-2 font-mono text-xs">
              <div>
                <span className="text-[10px] text-text-muted">Expected Return</span>
                <div className={`font-semibold ${trueVals.expectedReturnPct >= 0 ? 'text-green-emerald' : 'text-red-coral'}`}>
                  {formatReturnPct(trueVals.expectedReturnPct)}
                </div>
              </div>
              <div>
                <span className="text-[10px] text-text-muted">P(Up Move)</span>
                <div className="font-semibold text-blue-navy">
                  {(trueVals.probUp > 1 ? trueVals.probUp : trueVals.probUp * 100.0).toFixed(1)}%
                </div>
              </div>
            </div>

            <div className="space-y-1 text-xs">
              <div className="flex justify-between font-mono text-[11px]">
                <span className="text-text-muted">80% Interval:</span>
                <span className="text-blue-navy">
                  [{trueVals.interval80[0].toLocaleString()} - {trueVals.interval80[1].toLocaleString()}]
                </span>
              </div>
              <div className="flex justify-between font-mono text-[11px]">
                <span className="text-text-muted">95% Interval:</span>
                <span className="text-blue-navy">
                  [{trueVals.interval95[0].toLocaleString()} - {trueVals.interval95[1].toLocaleString()}]
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <span className={`inline-flex items-center gap-1 rounded px-2 py-0.5 font-mono text-[11px] font-medium ${
                trueVals.trendDir === 'positive'
                  ? 'bg-green-sage/30 text-green-emerald'
                  : trueVals.trendDir === 'negative'
                  ? 'bg-red-coral/20 text-red-coral'
                  : 'bg-surface-subtle text-text-muted'
              }`}>
                {renderTrendIcon(trueVals.trendDir)} {trueVals.trendArrow} {trueVals.trendDir}
              </span>
              <Sparkline data={truePanel.sparkline} width={80} height={20} color="#1B5CD6" />
            </div>
          </CardContent>
        </Card>

        {/* PANEL 3: If the news is FALSE */}
        <Card className="border-border bg-surface-white shadow-soft">
          <CardHeader className="border-b border-border/60 pb-2.5">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold text-text-primary">
                {falsePanel.name}
              </CardTitle>
              {/* Tooltip explaining FALSE means 'the event does not occur', exactly as API defines it */}
              <Tooltip content={`FALSE Scenario: ${meaning_of_false || 'the event does not occur'} (counterfactual status quo trajectory).`}>
                <span className="flex cursor-pointer items-center gap-1 text-[11px] font-medium text-amber-dark underline decoration-dotted">
                  Meaning of FALSE
                  <HelpCircle className="h-3.5 w-3.5" />
                </span>
              </Tooltip>
            </div>
            <p className="text-[11px] text-text-muted">
              {horizonLabels[selectedHorizon]} &bull; <span className="font-medium text-amber-dark">&ldquo;{meaning_of_false || 'the event does not occur'}&rdquo;</span>
            </p>
          </CardHeader>
          <CardContent className="space-y-3 pt-3">
            <div>
              <span className="text-[11px] font-medium text-text-muted">Projected ASPI Target</span>
              <div className="font-mono text-2xl font-bold text-text-primary">
                {falseVals.targetAspi.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 border-y border-border/50 py-2 font-mono text-xs">
              <div>
                <span className="text-[10px] text-text-muted">Expected Return</span>
                <div className={`font-semibold ${falseVals.expectedReturnPct >= 0 ? 'text-green-emerald' : 'text-red-coral'}`}>
                  {formatReturnPct(falseVals.expectedReturnPct)}
                </div>
              </div>
              <div>
                <span className="text-[10px] text-text-muted">P(Up Move)</span>
                <div className="font-semibold text-text-primary">
                  {(falseVals.probUp > 1 ? falseVals.probUp : falseVals.probUp * 100.0).toFixed(1)}%
                </div>
              </div>
            </div>

            <div className="space-y-1 text-xs">
              <div className="flex justify-between font-mono text-[11px]">
                <span className="text-text-muted">80% Interval:</span>
                <span className="text-text-secondary">
                  [{falseVals.interval80[0].toLocaleString()} - {falseVals.interval80[1].toLocaleString()}]
                </span>
              </div>
              <div className="flex justify-between font-mono text-[11px]">
                <span className="text-text-muted">95% Interval:</span>
                <span className="text-text-secondary">
                  [{falseVals.interval95[0].toLocaleString()} - {falseVals.interval95[1].toLocaleString()}]
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <span className={`inline-flex items-center gap-1 rounded px-2 py-0.5 font-mono text-[11px] font-medium ${
                falseVals.trendDir === 'positive'
                  ? 'bg-green-sage/30 text-green-emerald'
                  : falseVals.trendDir === 'negative'
                  ? 'bg-red-coral/20 text-red-coral'
                  : 'bg-surface-subtle text-text-muted'
              }`}>
                {renderTrendIcon(falseVals.trendDir)} {falseVals.trendArrow} {falseVals.trendDir}
              </span>
              <Sparkline data={falsePanel.sparkline} width={80} height={20} color="#718096" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
