import { Badge } from '@/components/ui/Badge';
import { Stepper, ELECTION_STAGES } from '@/components/ui/Stepper';
import type { TrajectoryDisplayMode } from '../types';

export interface EventStudyControlsProps {
  electionType: string;
  onElectionTypeChange: (type: string) => void;
  stageNumber: number;
  onStageNumberChange: (stageNum: number) => void;
  expectedReturnModel: string;
  onExpectedReturnModelChange: (model: string) => void;
  estimationWindow: number;
  onEstimationWindowChange: (len: number) => void;
  eventWindow: string;
  onEventWindowChange: (win: string) => void;
  includeOverlapping: boolean;
  onIncludeOverlappingChange: (include: boolean) => void;
  hasModelledTrajectory?: boolean;
  trajectoryDisplayMode?: TrajectoryDisplayMode;
  onTrajectoryDisplayModeChange?: (mode: TrajectoryDisplayMode) => void;
}

const ELECTION_TYPE_OPTIONS = ['All', 'Presidential', 'Parliamentary', 'Provincial'];

const EVENT_WINDOW_OPTIONS = [
  '[-2,+2]',
  '[-7,+7]',
  '[-7,-1]',
  '[0,+2]',
  '[0,+7]',
  '[0,+15]',
  '[0,+30]',
  '[-15,-1]',
  '[-30,-1]',
];

const ESTIMATION_WINDOW_OPTIONS = [15, 60, 120];

export function EventStudyControls({
  electionType,
  onElectionTypeChange,
  stageNumber,
  onStageNumberChange,
  expectedReturnModel,
  onExpectedReturnModelChange,
  estimationWindow,
  onEstimationWindowChange,
  eventWindow,
  onEventWindowChange,
  includeOverlapping,
  onIncludeOverlappingChange,
  hasModelledTrajectory = false,
  trajectoryDisplayMode = 'both',
  onTrajectoryDisplayModeChange,
}: EventStudyControlsProps) {
  return (
    <div className="bg-card border-border/80 space-y-4 rounded-xl border p-4 shadow-sm">
      {/* 1. Election Type Chips & Top Controls */}
      <div className="border-border/40 flex flex-wrap items-center justify-between gap-3 border-b pb-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-muted-foreground text-xs font-semibold uppercase tracking-wider">
            Election Type:
          </span>
          {ELECTION_TYPE_OPTIONS.map((type) => {
            const isSelected = electionType === type;
            return (
              <button
                key={type}
                type="button"
                onClick={() => onElectionTypeChange(type)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  isSelected
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                {type}
              </button>
            );
          })}
        </div>

        {/* Overlapping toggle */}
        <label className="flex cursor-pointer items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={includeOverlapping}
            onChange={(e) => onIncludeOverlappingChange(e.target.checked)}
            className="text-primary focus:ring-primary h-4 w-4 rounded border-gray-300"
          />
          <span className="text-muted-foreground">Include Overlapping Events (&le; 30 TD)</span>
        </label>
      </div>

      {/* 2. Six-stage Stepper Reused from F1 */}
      <div>
        <div className="mb-2 flex items-center justify-between">
          <span className="text-muted-foreground text-xs font-semibold uppercase tracking-wider">
            Electoral Stage Progression (t=0 Anchor):
          </span>
          <Badge variant="outline" className="text-xs">
            Step {stageNumber} of 6
          </Badge>
        </div>
        <Stepper
          currentStage={stageNumber}
          stages={ELECTION_STAGES}
          onStageClick={onStageNumberChange}
        />
      </div>

      {/* 3. Econometric Parameters: Model, Estimation Window, Event Window */}
      <div className="grid grid-cols-1 gap-4 pt-1 sm:grid-cols-2 lg:grid-cols-3">
        {/* Expected Return Model */}
        <div className="space-y-1.5">
          <label
            className="text-muted-foreground block text-xs font-medium"
            htmlFor="return-model-select"
          >
            Expected-Return Benchmark Model:
          </label>
          <select
            id="return-model-select"
            value={expectedReturnModel}
            onChange={(e) => onExpectedReturnModelChange(e.target.value)}
            className="border-input text-foreground focus:ring-primary h-9 w-full rounded-md border bg-background px-3 text-xs focus:outline-none focus:ring-1"
          >
            <option value="mean_adjusted">Constant-Mean Return Model</option>
            <option value="market_model_sp20">Market Model (S&amp;P SL 20 Benchmark)</option>
          </select>
        </div>

        {/* Estimation Window Length */}
        <div className="space-y-1.5">
          <label className="text-muted-foreground block text-xs font-medium">
            Estimation Window Length (L<sub>est</sub>):
          </label>
          <div className="flex gap-2">
            {ESTIMATION_WINDOW_OPTIONS.map((len) => (
              <button
                key={len}
                type="button"
                onClick={() => onEstimationWindowChange(len)}
                className={`flex-1 rounded-md border py-1.5 text-xs font-medium transition-colors ${
                  estimationWindow === len
                    ? 'border-primary bg-primary/10 text-primary font-semibold'
                    : 'border-input text-muted-foreground hover:bg-muted bg-background'
                }`}
              >
                {len} TD
              </button>
            ))}
          </div>
        </div>

        {/* Event Window */}
        <div className="space-y-1.5">
          <label
            className="text-muted-foreground block text-xs font-medium"
            htmlFor="event-window-select"
          >
            Event Window [t<sub>1</sub>, t<sub>2</sub>]:
          </label>
          <select
            id="event-window-select"
            value={eventWindow}
            onChange={(e) => onEventWindowChange(e.target.value)}
            className="border-input text-foreground focus:ring-primary h-9 w-full rounded-md border bg-background px-3 font-mono text-xs focus:outline-none focus:ring-1"
          >
            {EVENT_WINDOW_OPTIONS.map((win) => (
              <option key={win} value={win}>
                {win}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 4. Actual vs Model Trajectory Toggle (if API supplies modelled forecast) */}
      {hasModelledTrajectory && onTrajectoryDisplayModeChange ? (
        <div className="border-border/40 flex items-center justify-between border-t pt-3 text-xs">
          <span className="text-muted-foreground font-medium">Trajectory Overlay Mode:</span>
          <div className="flex rounded-lg border border-border p-0.5">
            {(['both', 'actual', 'predicted'] as TrajectoryDisplayMode[]).map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => onTrajectoryDisplayModeChange(mode)}
                className={`rounded-md px-3 py-1 font-medium capitalize transition-colors ${
                  trajectoryDisplayMode === mode
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {mode === 'both' ? 'Both' : mode === 'actual' ? 'Actual only' : 'Predicted only'}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="border-border/40 text-muted-foreground flex items-center justify-between border-t pt-2 text-xs">
          <span>Actual Trajectory: Grounded in Historical ASPI</span>
          <span className="italic">
            Econometric Model:{' '}
            {expectedReturnModel === 'mean_adjusted'
              ? 'Constant-Mean Return'
              : 'S&P SL 20 Benchmark'}
          </span>
        </div>
      )}
    </div>
  );
}
