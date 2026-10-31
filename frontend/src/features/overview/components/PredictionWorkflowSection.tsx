import React from 'react';
import { Layers, ShieldCheck, Sliders, Info } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Tooltip } from '@/components/ui/Tooltip';
import { useMeta } from '@/context/MetaContext';

export function PredictionWorkflowSection() {
  const { getMetricDefinition, getDisclaimer } = useMeta();

  const caarDef =
    getMetricDefinition('caar')?.definition ||
    'Accumulated abnormal return across [-3, +3] window compared against 10,000 placebo bootstrap draws.';
  const leakageNote =
    getDisclaimer('leakage') ||
    'Strict temporal embargo: all features computed strictly using t <= 0 historical information only.';

  const steps = [
    {
      number: '01',
      title: 'Event Window Definition & Embargo',
      icon: <Layers className="h-5 w-5 text-accent" />,
      summary:
        'Mapping election announcements, nominations, campaigns, and polling dates to Colombo trading days.',
      tooltip:
        'Trading days are mapped from Elections.csv with non-trading day alignment to next trading session (Rule R11).',
      metricRef: 'Event Calendar (146 Stages)',
    },
    {
      number: '02',
      title: 'Cumulative Abnormal Return (CAR) Estimation',
      icon: <Activity className="text-blue-primary h-5 w-5" />,
      summary:
        'Estimating abnormal returns against a 15-day pre-event estimation window with 10,000 placebo permutations.',
      tooltip: caarDef,
      metricRef: 'CAAR [-3, +3], [-10, +10]',
    },
    {
      number: '03',
      title: 'Feature Leakage Prevention Matrix',
      icon: <ShieldCheck className="text-success h-5 w-5" />,
      summary:
        'Standardizing features within walk-forward train folds only to enforce strict temporal causal boundaries.',
      tooltip: leakageNote,
      metricRef: 'Feature Sets A, B, C',
    },
    {
      number: '04',
      title: 'Counterfactual Walk-Forward Simulation',
      icon: <Sliders className="h-5 w-5 text-accent" />,
      summary:
        'Generating directional forecast distributions for conditional election scenarios and breaking news.',
      tooltip:
        'Walk-forward evaluation across P1 to P5 phases against naive random-walk baseline (Rule R3).',
      metricRef: 'Scenario Engine',
    },
  ];

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-heading text-xl font-bold text-text-primary">
            How the Prediction Works
          </h2>
          <p className="text-xs text-text-muted">
            The four-phase econometric protocol translating political events and breaking news into
            quantitative ASPI forecasts.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {steps.map((step) => (
          <Card
            key={step.number}
            className="relative flex flex-col justify-between p-5 transition-all duration-150 hover:shadow-card"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="text-accent/80 font-mono text-2xl font-black">{step.number}</span>
                <div className="flex h-9 w-9 items-center justify-center rounded-button bg-surface-subtle">
                  {step.icon}
                </div>
              </div>

              <div className="mt-3 flex items-start justify-between gap-1">
                <h3 className="font-heading text-sm font-bold text-text-primary">{step.title}</h3>
                <Tooltip content={step.tooltip}>
                  <button
                    type="button"
                    className="text-text-muted hover:text-text-primary focus:outline-none"
                    aria-label={`More details about ${step.title}`}
                  >
                    <Info className="h-3.5 w-3.5" />
                  </button>
                </Tooltip>
              </div>

              <p className="mt-2 text-xs leading-relaxed text-text-muted">{step.summary}</p>
            </div>

            <div className="border-border/60 mt-4 border-t pt-3">
              <span className="text-blue-primary font-mono text-[11px] font-medium dark:text-blue-vibrant">
                {step.metricRef}
              </span>
            </div>
          </Card>
        ))}
      </div>
    </section>
  );
}

function Activity(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  );
}
