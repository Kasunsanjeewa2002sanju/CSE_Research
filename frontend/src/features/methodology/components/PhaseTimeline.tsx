import React, { useState } from 'react';
import type { ProtocolPhase, TargetDefinition } from '../types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

interface PhaseTimelineProps {
  phases: ProtocolPhase[];
  targetDefinitions: TargetDefinition[];
}

export const PhaseTimeline: React.FC<PhaseTimelineProps> = ({ phases, targetDefinitions }) => {
  const [showTableView, setShowTableView] = useState(false);
  const [selectedPhaseId, setSelectedPhaseId] = useState<string>(phases[0]?.phase_id || 'P1');

  // Max span across all walk-forward folds is the full 7,635-trading-day longitudinal series
  const maxDays = Math.max(
    ...phases.map(
      (p) => (p.train_days ?? 0) + (p.embargo_days ?? 10) + (p.val_days ?? p.sample_size)
    ),
    7635
  );

  const selectedPhase = phases.find((p) => p.phase_id === selectedPhaseId) || phases[0];

  return (
    <div className="space-y-6">
      {/* 1. Header & Accessible Switch */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-foreground text-xl font-bold tracking-tight">
            Five-Phase Walk-Forward Protocol
          </h2>
          <p className="text-muted-foreground text-sm">
            Strict out-of-sample expanding window splits with 10-trading-day purged embargoes
            (Campbell, Lo & MacKinlay, 1997; Rule R2).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowTableView(!showTableView)}
            aria-label={showTableView ? 'Switch to Timeline Visual' : 'Switch to Table Data View'}
          >
            {showTableView ? 'Visual Timeline' : 'Data Table Alternative'}
          </Button>
        </div>
      </div>

      {/* 2. Visual Timeline or Accessible Table View */}
      {showTableView ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Walk-Forward Phase Boundaries & Sample Sizes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table
                className="w-full text-left text-xs"
                role="table"
                aria-label="Walk-Forward Fold Split Boundaries"
              >
                <thead>
                  <tr className="bg-muted/40 text-muted-foreground border-b border-border font-semibold">
                    <th className="p-3">Phase</th>
                    <th className="p-3">Training Window (Dates)</th>
                    <th className="p-3 text-right">Train Days</th>
                    <th className="p-3">Purged Embargo</th>
                    <th className="p-3 text-right">Embargo Days</th>
                    <th className="p-3">Validation Window (Dates)</th>
                    <th className="p-3 text-right">Val Days</th>
                    <th className="p-3 text-right">Inner Train / Val</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-mono">
                  {phases.map((phase) => (
                    <tr key={phase.phase_id} className="hover:bg-muted/20">
                      <td className="text-primary p-3 font-semibold">{phase.phase_id}</td>
                      <td className="p-3">
                        {phase.train_start ?? phase.start_date} to{' '}
                        {phase.train_end ?? phase.end_date}
                      </td>
                      <td className="p-3 text-right font-medium">
                        {phase.train_days?.toLocaleString() ?? '—'} TD
                      </td>
                      <td className="p-3 text-amber-600 dark:text-amber-400">
                        {phase.embargo_start} to {phase.embargo_end}
                      </td>
                      <td className="p-3 text-right text-amber-600 dark:text-amber-400">
                        {phase.embargo_days ?? 10} TD
                      </td>
                      <td className="p-3 text-cyan-600 dark:text-cyan-400">
                        {phase.val_start} to {phase.val_end}
                      </td>
                      <td className="p-3 text-right font-bold text-cyan-600 dark:text-cyan-400">
                        {phase.val_days?.toLocaleString() ?? phase.sample_size} TD
                      </td>
                      <td className="text-muted-foreground p-3 text-right">
                        {phase.inner_train_days ?? '—'} / {phase.inner_val_days ?? '—'} TD
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card padding="md">
          <div className="space-y-6">
            {/* Timeline Bars */}
            <div className="space-y-4" role="region" aria-label="Walk-Forward Timeline Diagram">
              {phases.map((phase) => {
                const trainDays = phase.train_days ?? 4299;
                const embargoDays = phase.embargo_days ?? 10;
                const valDays = phase.val_days ?? phase.sample_size;

                const trainPct = Math.max(5, (trainDays / maxDays) * 100);
                const embargoPct = Math.max(1, (embargoDays / maxDays) * 100);
                const valPct = Math.max(4, (valDays / maxDays) * 100);
                const isSelected = phase.phase_id === selectedPhaseId;

                return (
                  <div
                    key={phase.phase_id}
                    onClick={() => setSelectedPhaseId(phase.phase_id)}
                    className={`cursor-pointer rounded-lg border p-3.5 transition-all ${
                      isSelected
                        ? 'border-primary bg-primary/5 ring-primary/30 shadow-sm ring-1'
                        : 'border-border/60 hover:bg-muted/10 hover:border-border'
                    }`}
                    tabIndex={0}
                    role="button"
                    aria-label={`Select ${phase.name}`}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        setSelectedPhaseId(phase.phase_id);
                      }
                    }}
                  >
                    <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={isSelected ? 'default' : 'outline'}
                          className="font-mono text-xs"
                        >
                          {phase.phase_id}
                        </Badge>
                        <span className="text-foreground text-sm font-semibold">{phase.name}</span>
                      </div>
                      <div className="text-muted-foreground flex items-center gap-3 font-mono text-xs">
                        <span>
                          Total:{' '}
                          <strong className="text-foreground">
                            {trainDays + embargoDays + valDays}
                          </strong>{' '}
                          TD
                        </span>
                        <span>
                          Val:{' '}
                          <strong className="text-cyan-600 dark:text-cyan-400">{valDays}</strong> TD
                        </span>
                      </div>
                    </div>

                    {/* Proportional Stacked Segment Bar */}
                    <div className="bg-muted/30 relative flex h-8 w-full overflow-hidden rounded-md">
                      {/* 1. Expanding Training Window Bar */}
                      <div
                        style={{ width: `${trainPct}%` }}
                        className="flex items-center justify-between overflow-hidden bg-gradient-to-r from-[#0A2A66] to-[#1C4EAA] px-2 text-[10px] font-medium text-white shadow-inner"
                        title={`Training Window: ${phase.train_start} to ${phase.train_end} (${trainDays} trading days)`}
                      >
                        <span className="truncate">
                          Train: {phase.train_start?.slice(0, 4)}–{phase.train_end?.slice(0, 4)}
                        </span>
                        <span className="font-mono opacity-80">{trainDays} TD</span>
                      </div>

                      {/* 2. Purged Embargo Gap Bar */}
                      <div
                        style={{ width: `${embargoPct}%`, minWidth: '8px' }}
                        className="flex items-center justify-center bg-amber-500/80 text-[10px] font-bold text-amber-950 dark:text-amber-100"
                        title={`10-Trading-Day Purged Embargo: ${phase.embargo_start} to ${phase.embargo_end}`}
                      >
                        <span className="sr-only">Embargo 10 TD</span>
                      </div>

                      {/* 3. Validation Window Bar */}
                      <div
                        style={{ width: `${valPct}%` }}
                        className="flex items-center justify-between overflow-hidden bg-gradient-to-r from-[#0095B3] to-[#00B4D8] px-2 text-[10px] font-medium text-white"
                        title={`Validation Window: ${phase.val_start} to ${phase.val_end} (${valDays} trading days)`}
                      >
                        <span className="truncate">
                          Val: {phase.val_start?.slice(0, 4)}–{phase.val_end?.slice(0, 4)}
                        </span>
                        <span className="font-mono">{valDays} TD</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Selected Phase Detail Callout */}
            {selectedPhase && (
              <div className="border-border/80 bg-muted/20 rounded-lg border p-4">
                <div className="mb-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-primary font-mono text-xs font-bold uppercase">
                      {selectedPhase.phase_id} Context
                    </span>
                    <span className="text-foreground text-sm font-semibold">
                      {selectedPhase.name}
                    </span>
                  </div>
                  <span className="text-muted-foreground font-mono text-xs">
                    Embargo:{' '}
                    <strong className="text-amber-600 dark:text-amber-400">
                      {selectedPhase.embargo_days ?? 10} TD
                    </strong>
                  </span>
                </div>
                <p className="text-muted-foreground text-xs">{selectedPhase.description}</p>
                <div className="mt-3 grid grid-cols-2 gap-2 font-mono text-[11px] sm:grid-cols-4">
                  <div className="border-border/50 bg-background/50 rounded border p-2">
                    <span className="text-muted-foreground">Train Span:</span>
                    <div className="text-foreground font-semibold">
                      {selectedPhase.train_start} &rarr; {selectedPhase.train_end}
                    </div>
                  </div>
                  <div className="border-border/50 bg-background/50 rounded border p-2">
                    <span className="text-muted-foreground">Purged Embargo:</span>
                    <div className="font-semibold text-amber-600 dark:text-amber-400">
                      {selectedPhase.embargo_start} &rarr; {selectedPhase.embargo_end}
                    </div>
                  </div>
                  <div className="border-border/50 bg-background/50 rounded border p-2">
                    <span className="text-muted-foreground">Validation Span:</span>
                    <div className="font-semibold text-cyan-600 dark:text-cyan-400">
                      {selectedPhase.val_start} &rarr; {selectedPhase.val_end}
                    </div>
                  </div>
                  <div className="border-border/50 bg-background/50 rounded border p-2">
                    <span className="text-muted-foreground">Inner Train / Val:</span>
                    <div className="text-foreground font-semibold">
                      {selectedPhase.inner_train_days ?? '—'} /{' '}
                      {selectedPhase.inner_val_days ?? '—'} TD
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* 3. Target Definitions (Horizons, Continuous Return, Binary Direction) */}
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <CardTitle className="text-base">
                Prediction Target Definitions & Forecasting Horizons
              </CardTitle>
              <p className="text-muted-foreground text-xs">
                All models predict forward logarithmic return (r_t+h) and binary market direction
                (y_t+h) across 3 canonical trading horizons.
              </p>
            </div>
            <Badge variant="outline" className="font-mono text-xs">
              Rule R4 Grounded
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {targetDefinitions.map((target) => (
              <div
                key={target.target_id}
                className="bg-card flex flex-col justify-between rounded-lg border border-border p-4 shadow-sm"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <Badge variant="secondary" className="text-primary font-mono text-xs font-bold">
                      {target.horizon_label || `h = ${target.horizon_days} TD`}
                    </Badge>
                    <span className="text-muted-foreground font-mono text-[11px]">
                      {target.target_id}
                    </span>
                  </div>
                  <h3 className="text-foreground mt-2 text-sm font-semibold">
                    {target.name || `${target.horizon_days}-Day Target`}
                  </h3>
                  <p className="text-muted-foreground mt-1 text-xs">{target.description}</p>
                </div>

                <div className="border-border/60 mt-4 space-y-2 border-t pt-3 font-mono text-xs">
                  <div>
                    <span className="text-muted-foreground font-sans text-[11px] font-medium">
                      Continuous Return Target:
                    </span>
                    <div className="bg-muted/40 text-foreground mt-0.5 rounded p-1.5 font-semibold">
                      {target.return_formula || target.formula}
                    </div>
                  </div>
                  <div>
                    <span className="text-muted-foreground font-sans text-[11px] font-medium">
                      Direction Target:
                    </span>
                    <div className="bg-muted/40 text-foreground mt-0.5 rounded p-1.5">
                      {target.direction_formula || `sign(r_{t+${target.horizon_days}}) in {+1, -1}`}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
