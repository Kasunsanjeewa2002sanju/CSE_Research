import React, { useState, useMemo } from 'react';
import type { BaselineDefinition } from '../types';
import type { MetricGlossaryItem } from '@/api/types';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

interface BaselinesGlossaryProps {
  baselines: BaselineDefinition[];
  metrics: MetricGlossaryItem[];
}

export const BaselinesGlossary: React.FC<BaselinesGlossaryProps> = ({ baselines, metrics }) => {
  const [metricSearch, setMetricSearch] = useState('');

  const filteredMetrics = useMemo(() => {
    if (!metricSearch.trim()) return metrics;
    const q = metricSearch.toLowerCase();
    return metrics.filter(
      (m) =>
        m.name.toLowerCase().includes(q) ||
        m.definition.toLowerCase().includes(q) ||
        (m.formula ?? '').toLowerCase().includes(q) ||
        (m.benchmark ?? '').toLowerCase().includes(q)
    );
  }, [metrics, metricSearch]);

  return (
    <div className="space-y-8">
      {/* 1. Header */}
      <div>
        <h2 className="text-foreground text-xl font-bold tracking-tight">
          Econometric Baselines & Statistical Metrics Glossary
        </h2>
        <p className="text-muted-foreground text-sm">
          Mathematical definitions, directional classification rules, and academic interpretations
          from the research glossary.
        </p>
      </div>

      {/* 2. Baselines Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-foreground text-base font-bold">
            Reference Benchmark Models (Stage 6 Baselines)
          </h3>
          <Badge variant="outline" className="font-mono text-xs">
            Stage 6 Verified
          </Badge>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {baselines.map((base) => (
            <Card key={base.id} padding="md" className="flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2">
                  <Badge variant="secondary" className="text-primary font-mono text-xs font-bold">
                    {base.id}
                  </Badge>
                  <span className="text-muted-foreground font-mono text-[10px]">
                    Benchmark Anchor
                  </span>
                </div>
                <h4 className="text-foreground mt-2 text-sm font-bold">{base.name}</h4>
                <p className="text-muted-foreground mt-1 text-xs">{base.definition}</p>

                {/* Mathematical Formula & Direction Rule */}
                <div className="bg-muted/30 mt-3 space-y-2 rounded-md p-2.5 font-mono text-xs">
                  <div>
                    <span className="text-muted-foreground font-sans text-[10px] font-semibold uppercase">
                      Forecasting Formula:
                    </span>
                    <div className="text-foreground mt-0.5 font-semibold">{base.formula}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground font-sans text-[10px] font-semibold uppercase">
                      Direction Rule:
                    </span>
                    <div className="text-muted-foreground mt-0.5">{base.direction_rule}</div>
                  </div>
                </div>
              </div>

              {/* Economic Interpretation & Benchmark Role */}
              <div className="border-border/50 mt-4 border-t pt-3 text-xs">
                <div className="text-muted-foreground">
                  <span className="text-foreground font-semibold">Academic Interpretation: </span>
                  {base.interpretation}
                </div>
                <div className="text-primary mt-1 font-mono text-[11px] font-medium">
                  Role: {base.benchmark_role}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* 3. Metrics Glossary Section */}
      <div className="space-y-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-foreground text-base font-bold">
              Statistical Evaluation Metrics Glossary
            </h3>
            <p className="text-muted-foreground text-xs">
              Rigorous econometric formulas for performance verification, unit roots, and hypothesis
              testing.
            </p>
          </div>
          <div className="w-full sm:w-64">
            <input
              type="text"
              placeholder="Search metrics..."
              value={metricSearch}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMetricSearch(e.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              aria-label="Search econometric metrics"
            />
          </div>
        </div>

        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table
                className="w-full text-left text-xs"
                role="table"
                aria-label="Metrics Glossary Table"
              >
                <thead>
                  <tr className="bg-muted/40 text-muted-foreground border-b border-border font-semibold">
                    <th className="p-3">Metric Name</th>
                    <th className="p-3">Mathematical Formula</th>
                    <th className="p-3">Benchmark & Criterion</th>
                    <th className="p-3">Academic Interpretation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredMetrics.map((metric) => (
                    <tr key={metric.metric_id} className="hover:bg-muted/20">
                      <td className="p-3 align-top">
                        <div className="text-foreground font-semibold">{metric.name}</div>
                        <div className="text-muted-foreground font-mono text-[10px]">
                          {metric.metric_id}
                        </div>
                      </td>
                      <td className="text-primary p-3 align-top font-mono text-[11px]">
                        {metric.formula || '—'}
                      </td>
                      <td className="text-muted-foreground p-3 align-top font-mono text-[11px]">
                        {metric.benchmark || '—'}
                      </td>
                      <td className="text-foreground/90 max-w-sm p-3 align-top">
                        {metric.definition}
                      </td>
                    </tr>
                  ))}
                  {filteredMetrics.length === 0 && (
                    <tr>
                      <td colSpan={4} className="text-muted-foreground p-8 text-center">
                        No metrics matching &ldquo;{metricSearch}&rdquo;
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
