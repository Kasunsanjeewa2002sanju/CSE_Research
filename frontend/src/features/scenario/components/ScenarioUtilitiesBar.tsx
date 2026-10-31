import { useState } from 'react';
import { Share2, Download, Printer, History, Check, FileJson } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Drawer } from '@/components/ui/Drawer';
import type { ScenarioSubmitResponse, ScenarioRunRecord } from '../types';

export interface ScenarioUtilitiesBarProps {
  result: ScenarioSubmitResponse;
  sessionHistory: ScenarioRunRecord[];
  onRestoreRun: (runId: string) => void;
}

export function ScenarioUtilitiesBar({
  result,
  sessionHistory,
  onRestoreRun,
}: ScenarioUtilitiesBarProps) {
  const [copiedPermalink, setCopiedPermalink] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  // 1. Permalink Generator
  const handleCopyPermalink = () => {
    try {
      const url = new URL(window.location.origin + window.location.pathname);
      url.searchParams.set('headline', result.headline);
      url.searchParams.set('date', result.publication_date);
      url.searchParams.set('category', result.category);
      if (result.stage && result.stage !== 'none') {
        url.searchParams.set('stage', result.stage);
      }
      navigator.clipboard.writeText(url.toString());
      setCopiedPermalink(true);
      setTimeout(() => setCopiedPermalink(false), 2500);
    } catch {
      // Fallback
    }
  };

  // 2. Export JSON
  const handleExportJSON = () => {
    const jsonBlob = new Blob([JSON.stringify(result, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(jsonBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scenario_${result.scenario_id}_${result.publication_date}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // 3. Export PDF via print-friendly stylesheet
  const handleExportPDF = () => {
    window.print();
  };

  // 4. Export PNG chart / summary
  const handleExportPNG = () => {
    try {
      const chartCanvas = document.querySelector('canvas');
      if (chartCanvas) {
        const imageURL = chartCanvas.toDataURL('image/png');
        const a = document.createElement('a');
        a.href = imageURL;
        a.download = `scenario_fan_chart_${result.scenario_id}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      } else {
        window.print();
      }
    } catch {
      window.print();
    }
  };

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-surface-white p-3 shadow-soft print:hidden">
        <div className="flex items-center gap-2">
          {/* Permalink button */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleCopyPermalink}
            className="flex items-center gap-1.5 text-xs"
          >
            {copiedPermalink ? <Check className="h-3.5 w-3.5 text-green-emerald" /> : <Share2 className="h-3.5 w-3.5" />}
            {copiedPermalink ? 'Link Copied!' : 'Permalink'}
          </Button>

          {/* Session history button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsHistoryOpen(true)}
            className="flex items-center gap-1.5 text-xs"
          >
            <History className="h-3.5 w-3.5 text-text-muted" />
            Session Runs ({sessionHistory.length})
          </Button>
        </div>

        {/* Export Action Buttons */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportPNG}
            className="flex items-center gap-1.5 text-xs text-text-secondary"
          >
            <Download className="h-3.5 w-3.5" />
            PNG Chart
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleExportPDF}
            className="flex items-center gap-1.5 text-xs text-text-secondary"
          >
            <Printer className="h-3.5 w-3.5" />
            Print / PDF
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleExportJSON}
            className="flex items-center gap-1.5 text-xs text-text-secondary"
          >
            <FileJson className="h-3.5 w-3.5" />
            Export JSON
          </Button>
        </div>
      </div>

      {/* Session History Slide-Over Drawer */}
      <Drawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        title={`Session Simulation History (${sessionHistory.length} Runs)`}
      >
        <div className="space-y-3 p-4">
          <p className="text-xs text-text-muted">
            In-memory history of scenario runs executed during your active session. Click any past run to restore its predictions.
          </p>

          {sessionHistory.length === 0 ? (
            <div className="py-8 text-center text-xs text-text-muted">
              No historical runs recorded in this session yet.
            </div>
          ) : (
            <div className="divide-y divide-border/60">
              {sessionHistory.map((run) => (
                <div
                  key={run.id}
                  className="cursor-pointer py-3 transition-colors hover:bg-surface-subtle/40"
                  onClick={() => {
                    onRestoreRun(run.id);
                    setIsHistoryOpen(false);
                  }}
                >
                  <div className="flex items-center justify-between text-[11px] text-text-muted">
                    <span className="font-mono">{run.timestamp}</span>
                    <span className="rounded bg-surface-subtle px-1.5 py-0.5 capitalize">{run.category}</span>
                  </div>
                  <div className="mt-1 line-clamp-2 text-xs font-semibold text-text-primary">
                    {run.headline}
                  </div>
                  <div className="mt-1.5 flex items-center justify-between font-mono text-[11px]">
                    <span className="text-blue-navy">
                      TRUE: {run.trueReturnPct >= 0 ? '+' : ''}{run.trueReturnPct.toFixed(2)}% (~{run.targetAspi.toFixed(0)})
                    </span>
                    <span className="text-text-muted">
                      FALSE: {run.falseReturnPct >= 0 ? '+' : ''}{run.falseReturnPct.toFixed(2)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Drawer>
    </>
  );
}
