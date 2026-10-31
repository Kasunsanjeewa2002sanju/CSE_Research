import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface StepItem {
  id: string;
  number: number;
  label: string;
  description?: string;
  windowDays?: string; // e.g. "t < -30", "[-14, 0]"
}

export const ELECTION_STAGES: StepItem[] = [
  {
    id: 'announcement',
    number: 1,
    label: 'Proclamation',
    windowDays: 't < -30',
    description: 'Gazette announcement of election date',
  },
  {
    id: 'nomination',
    number: 2,
    label: 'Nominations',
    windowDays: '[-30, -14]',
    description: 'Candidate submission & party manifests',
  },
  {
    id: 'campaign',
    number: 3,
    label: 'Campaign Window',
    windowDays: '[-14, 0]',
    description: 'Rallies & media polling intensity',
  },
  {
    id: 'polling-day',
    number: 4,
    label: 'Polling Day',
    windowDays: 't = 0',
    description: 'National vote casting & trading silence',
  },
  {
    id: 'results',
    number: 5,
    label: 'Results Declaration',
    windowDays: '[0, +5]',
    description: 'Immediate abnormal return reaction',
  },
  {
    id: 'regime-settlement',
    number: 6,
    label: 'Regime Settlement',
    windowDays: '[+5, +30]',
    description: 'Cabinet formation & policy horizon',
  },
];

export interface StepperProps {
  currentStep?: number; // 1-indexed (1 to 6)
  currentStage?: number;
  onStepClick?: (stepNumber: number) => void;
  onStageClick?: (stageNumber: number) => void;
  stages?: StepItem[];
  className?: string;
}

export function Stepper({
  currentStep,
  currentStage,
  onStepClick,
  onStageClick,
  stages = ELECTION_STAGES,
  className,
}: StepperProps) {
  const activeStep = currentStage !== undefined ? currentStage : (currentStep ?? 1);
  const handleStepClick = onStageClick || onStepClick;

  return (
    <nav aria-label="Election Stages Progress" className={cn('w-full', className)}>
      <ol className="grid grid-cols-2 gap-2 md:grid-cols-6 md:gap-3">
        {stages.map((stage) => {
          const isCompleted = stage.number < activeStep;
          const isCurrent = stage.number === activeStep;
          const isUpcoming = stage.number > activeStep;

          return (
            <li
              key={stage.id}
              className={cn(
                'transition-standard relative flex flex-col justify-between rounded-card border p-3',
                isCompleted &&
                  'bg-blue-ice/40 dark:bg-blue-soft/10 border-blue-soft text-text-primary',
                isCurrent &&
                  'bg-accent/10 border-accent text-text-primary shadow-soft ring-1 ring-accent',
                isUpcoming && 'border-border/60 bg-surface-subtle/30 text-text-muted opacity-60',
                handleStepClick && 'cursor-pointer hover:border-border-strong'
              )}
              onClick={() => handleStepClick?.(stage.number)}
              tabIndex={handleStepClick ? 0 : undefined}
              role={handleStepClick ? 'button' : undefined}
              aria-current={isCurrent ? 'step' : undefined}
            >
              <div className="mb-1.5 flex items-center justify-between gap-1">
                <span
                  className={cn(
                    'flex h-5 w-5 items-center justify-center rounded-full font-mono text-[10px] font-bold',
                    isCompleted && 'bg-blue-navy text-white',
                    isCurrent && 'bg-accent text-accent-foreground',
                    isUpcoming && 'bg-border text-text-muted'
                  )}
                >
                  {isCompleted ? <Check className="h-3 w-3 stroke-[3]" /> : stage.number}
                </span>

                {stage.windowDays && (
                  <span className="border-border/60 rounded border bg-surface-white px-1.5 py-0.5 font-mono text-[10px] text-text-muted">
                    {stage.windowDays}
                  </span>
                )}
              </div>

              <div>
                <div className="line-clamp-1 font-heading text-xs font-semibold text-text-primary">
                  {stage.label}
                </div>
                {stage.description && (
                  <p className="mt-0.5 line-clamp-1 font-sans text-[10px] text-text-muted">
                    {stage.description}
                  </p>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
