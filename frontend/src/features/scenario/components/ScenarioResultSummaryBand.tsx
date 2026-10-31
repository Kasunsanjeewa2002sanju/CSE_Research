import { AlertTriangle, Info, CheckCircle2, ShieldAlert } from 'lucide-react';
import type { ScenarioSubmitResponse } from '../types';

export interface ScenarioResultSummaryBandProps {
  result: ScenarioSubmitResponse;
}

export function ScenarioResultSummaryBand({ result }: ScenarioResultSummaryBandProps) {
  const {
    category_label,
    stage_label,
    expected_direction,
    expected_direction_arrow,
    expected_direction_sign,
    evidence_strength,
    is_stale,
    stale_warning,
    is_material_impact,
    material_impact_summary,
    disclaimer,
  } = result;

  // Color mapping based on direction
  const directionClasses = {
    positive: 'bg-green-sage/20 text-green-emerald border-green-emerald/30',
    negative: 'bg-red-coral/15 text-red-coral border-red-coral/30',
    neutral: 'bg-surface-subtle text-text-muted border-border',
    uncertain: 'bg-amber-soft/20 text-amber-dark border-amber-soft/40',
  }[expected_direction] || 'bg-surface-subtle text-text-muted border-border';

  // Color mapping for evidence strength
  const strengthClasses = {
    strong: 'bg-green-sage/20 text-green-emerald border-green-emerald/40',
    moderate: 'bg-amber-soft/20 text-amber-dark border-amber-soft/50',
    weak: 'bg-surface-subtle text-text-muted border-border',
  }[evidence_strength.toLowerCase()] || 'bg-surface-subtle text-text-muted border-border';

  return (
    <div className="space-y-3">
      {/* 1. Stale Data Warning Banner (Rule FR5 Honest UI) */}
      {is_stale && (
        <div
          role="alert"
          className="flex items-start gap-2.5 rounded-lg border border-amber-soft/60 bg-amber-soft/15 p-3 text-xs text-amber-dark"
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <div className="space-y-0.5">
            <span className="font-semibold">Market Baseline Warning:</span>{' '}
            <span>{stale_warning || 'Scenario date is beyond historical database records. Forecast anchored to latest available close.'}</span>
          </div>
        </div>
      )}

      {/* 2. Irrelevant News Warning Banner (Rule FR5 Honest UI) */}
      {!is_material_impact && (
        <div
          role="alert"
          className="flex items-start gap-2.5 rounded-lg border border-border/80 bg-surface-subtle/80 p-3 text-xs text-text-secondary"
        >
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-text-muted" />
          <div className="space-y-0.5">
            <span className="font-semibold text-text-primary">No Material Impact Detected:</span>{' '}
            <span>{material_impact_summary}</span>
          </div>
        </div>
      )}

      {/* 3. Core Result Summary Band */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-surface-white p-3.5 shadow-soft">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-text-muted">Classification:</span>

          {/* Category Chip */}
          <span className="inline-flex items-center rounded-md border border-blue-soft/50 bg-blue-ice/30 px-2.5 py-1 text-xs font-medium text-blue-navy">
            {category_label}
          </span>

          {/* Stage Chip */}
          <span className="inline-flex items-center rounded-md border border-border bg-surface-subtle px-2.5 py-1 text-xs font-medium text-text-secondary">
            Stage: {stage_label}
          </span>

          {/* Expected Direction Chip */}
          <span
            className={`inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-semibold uppercase tracking-wider font-mono ${directionClasses}`}
          >
            <span>{expected_direction_arrow}</span>
            <span>{expected_direction_sign} {expected_direction}</span>
          </span>

          {/* Evidence Strength Chip */}
          <span
            className={`inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-semibold uppercase font-mono ${strengthClasses}`}
          >
            <ShieldAlert className="h-3 w-3" />
            <span>Evidence: {evidence_strength}</span>
          </span>
        </div>

        {/* Status validation */}
        <div className="flex items-center gap-1.5 text-xs text-green-emerald">
          <CheckCircle2 className="h-4 w-4" />
          <span className="font-medium">Econometrically Calibrated</span>
        </div>
      </div>

      {/* 4. Mandatory Academic Disclaimer (Rule FR5 Honest UI) */}
      <div className="flex items-center justify-between rounded-md border border-border/60 bg-surface-subtle/40 px-3 py-1.5 text-[11px] text-text-muted">
        <span className="italic">
          <strong>Academic Disclaimer:</strong> {disclaimer}
        </span>
        <span className="font-mono text-[10px] text-text-muted/80">Walk-Forward Conformal Residuals</span>
      </div>
    </div>
  );
}
