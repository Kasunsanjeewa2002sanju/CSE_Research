import React, { useState } from 'react';
import type { PipelineStage } from '../types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

interface PipelineFlowProps {
  stages: PipelineStage[];
}

export const PipelineFlow: React.FC<PipelineFlowProps> = ({ stages }) => {
  const [selectedStageId, setSelectedStageId] = useState<string>(stages[0]?.stage_id || 'stage_0');
  const [showTableView, setShowTableView] = useState(false);

  const selectedStage = stages.find((s) => s.stage_id === selectedStageId) || stages[0];

  // Group stages into logical pipeline tiers
  const tiers = [
    {
      title: 'Tier 1: Ingestion & Setup',
      stages: stages.filter((s) => [0, 1, 2, 3, 10].includes(s.stage_number)),
    },
    {
      title: 'Tier 2: Event Study & Features',
      stages: stages.filter((s) => [4, 5].includes(s.stage_number)),
    },
    {
      title: 'Tier 3: Model Training',
      stages: stages.filter((s) => [6, 8].includes(s.stage_number)),
    },
    {
      title: 'Tier 4: Statistical Evaluation',
      stages: stages.filter((s) => [9, 11].includes(s.stage_number)),
    },
    {
      title: 'Tier 5: Audit & Synthesis',
      stages: stages.filter((s) => [12, 13].includes(s.stage_number)),
    },
  ];

  return (
    <div className="space-y-6">
      {/* 1. Header & Accessible Switch */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-foreground text-xl font-bold tracking-tight">
            Backend Pipeline Execution Architecture
          </h2>
          <p className="text-muted-foreground text-sm">
            End-to-end directed flow graph of all 13 research stages (0 to 13) verified from
            pipeline execution logs.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowTableView(!showTableView)}
            aria-label={showTableView ? 'Switch to SVG Flow Diagram' : 'Switch to Table Data View'}
          >
            {showTableView ? 'Interactive Diagram' : 'Stage Table View'}
          </Button>
        </div>
      </div>

      {/* 2. Interactive SVG Flow or Accessible Table */}
      {showTableView ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Backend Stages Status & Reports</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table
                className="w-full text-left text-xs"
                role="table"
                aria-label="Backend Stages Table"
              >
                <thead>
                  <tr className="bg-muted/40 text-muted-foreground border-b border-border font-semibold">
                    <th className="p-3">Stage</th>
                    <th className="p-3">Stage Name</th>
                    <th className="p-3">Category</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Last Run Time</th>
                    <th className="p-3">Summary</th>
                    <th className="p-3">Stage Report</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {stages.map((stage) => (
                    <tr key={stage.stage_id} className="hover:bg-muted/20">
                      <td className="text-primary p-3 font-mono font-bold">
                        Stage {stage.stage_number}
                      </td>
                      <td className="text-foreground p-3 font-medium">{stage.name}</td>
                      <td className="text-muted-foreground p-3">{stage.category}</td>
                      <td className="p-3">
                        <Badge
                          variant="outline"
                          className="text-xs uppercase text-teal-600 dark:text-teal-400"
                        >
                          {stage.status}
                        </Badge>
                      </td>
                      <td className="text-muted-foreground p-3 font-mono">{stage.last_run_time}</td>
                      <td className="text-muted-foreground max-w-xs p-3">{stage.summary}</td>
                      <td className="p-3">
                        <a
                          href={stage.report_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary font-mono text-xs underline hover:text-accent"
                        >
                          {stage.report_title}
                        </a>
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
            {/* SVG Interactive Multi-Tier Flow Diagram */}
            <div
              className="border-border/80 bg-background/50 relative w-full overflow-x-auto rounded-lg border p-4"
              role="region"
              aria-label="Accessible SVG Flow Diagram of Backend Stages"
            >
              <div className="min-w-[900px] space-y-6">
                {tiers.map((tier, tierIdx) => (
                  <div key={tier.title} className="relative space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground font-mono text-[11px] font-bold uppercase tracking-wider">
                        {tier.title}
                      </span>
                      <div className="bg-border/60 h-px flex-1" />
                    </div>

                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
                      {tier.stages.map((stage) => {
                        const isSelected = stage.stage_id === selectedStageId;
                        return (
                          <div
                            key={stage.stage_id}
                            onClick={() => setSelectedStageId(stage.stage_id)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' || e.key === ' ') {
                                setSelectedStageId(stage.stage_id);
                              }
                            }}
                            tabIndex={0}
                            role="button"
                            aria-label={`Inspect Stage ${stage.stage_number}: ${stage.name}`}
                            className={`group relative flex flex-col justify-between rounded-lg border p-3 text-left transition-all ${
                              isSelected
                                ? 'border-primary bg-primary/5 ring-primary/40 shadow-sm ring-2'
                                : 'border-border/70 bg-card hover:bg-muted/30 hover:border-border'
                            }`}
                          >
                            <div>
                              <div className="flex items-center justify-between gap-1">
                                <Badge
                                  variant={isSelected ? 'default' : 'secondary'}
                                  className="font-mono text-[10px] font-bold"
                                >
                                  S{stage.stage_number}
                                </Badge>
                                <span className="flex items-center gap-1 font-mono text-[10px] text-teal-600 dark:text-teal-400">
                                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-teal-500" />
                                  {stage.status}
                                </span>
                              </div>
                              <h3 className="text-foreground group-hover:text-primary mt-1.5 line-clamp-2 text-xs font-semibold">
                                {stage.name}
                              </h3>
                            </div>

                            <div className="border-border/50 text-muted-foreground mt-3 border-t pt-2 font-mono text-[10px]">
                              <span>Run: {stage.last_run_time.slice(0, 10)}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* SVG Connector Downward Indicator for Sequential Flow */}
                    {tierIdx < tiers.length - 1 && (
                      <div className="flex justify-center py-1">
                        <svg
                          width="24"
                          height="16"
                          viewBox="0 0 24 16"
                          className="text-muted-foreground/40"
                        >
                          <path
                            d="M12 0 L12 12 M7 8 L12 13 L17 8"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                          />
                        </svg>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Selected Stage Detail Inspector */}
            {selectedStage && (
              <div className="border-primary/30 bg-primary/5 rounded-lg border p-4">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="default" className="font-mono text-xs">
                      Stage {selectedStage.stage_number}
                    </Badge>
                    <h3 className="text-foreground text-base font-bold">{selectedStage.name}</h3>
                    <Badge variant="outline" className="text-xs">
                      {selectedStage.category}
                    </Badge>
                  </div>
                  <div className="text-muted-foreground flex items-center gap-2 font-mono text-xs">
                    <span>
                      Status:{' '}
                      <strong className="uppercase text-teal-600 dark:text-teal-400">
                        {selectedStage.status}
                      </strong>
                    </span>
                    <span>&bull;</span>
                    <span>Last Run: {selectedStage.last_run_time}</span>
                  </div>
                </div>

                <p className="text-foreground/90 mt-2 text-sm">{selectedStage.summary}</p>

                <div className="border-border/60 mt-4 flex flex-wrap items-center justify-between gap-3 border-t pt-3">
                  <div className="text-muted-foreground flex items-center gap-2 font-mono text-xs">
                    <span>Dependencies:</span>
                    {selectedStage.dependencies.length > 0 ? (
                      selectedStage.dependencies.map((dep) => (
                        <Badge key={dep} variant="secondary" className="font-mono text-[10px]">
                          {dep}
                        </Badge>
                      ))
                    ) : (
                      <span className="italic">None (Root Stage)</span>
                    )}
                  </div>

                  <a
                    href={selectedStage.report_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bg-primary hover:bg-primary/90 focus-visible:outline-primary inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold text-white shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
                  >
                    <span>View Stage Report ({selectedStage.report_title})</span>
                    <svg
                      width="12"
                      height="12"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                      <polyline points="15 3 21 3 21 9" />
                      <line x1="10" y1="14" x2="21" y2="3" />
                    </svg>
                  </a>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};
