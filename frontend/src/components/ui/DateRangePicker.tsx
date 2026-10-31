import { useState, useEffect } from 'react';
import { Calendar, ChevronRight } from 'lucide-react';
import { Button } from './Button';
import { cn } from '@/lib/utils';

export interface DateRange {
  startDate: string;
  endDate: string;
}

export interface DateRangePreset {
  label: string;
  startDate: string;
  endDate: string;
}

export interface DateRangePickerProps {
  value?: DateRange;
  startDate?: string;
  endDate?: string;
  onChange?: ((range: DateRange) => void) | ((startDate: string, endDate: string) => void);
  presets?: DateRangePreset[];
  className?: string;
}

const DEFAULT_PRESETS: DateRangePreset[] = [
  { label: 'YTD', startDate: '2024-01-01', endDate: '2024-09-30' },
  { label: '1 Year', startDate: '2023-10-01', endDate: '2024-09-30' },
  { label: '5 Years', startDate: '2019-10-01', endDate: '2024-09-30' },
  { label: 'All History', startDate: '2010-01-01', endDate: '2024-09-30' },
];

export function DateRangePicker({
  value,
  startDate = '2024-01-01',
  endDate = '2024-09-30',
  onChange,
  presets = DEFAULT_PRESETS,
  className,
}: DateRangePickerProps) {
  const currentStart = value?.startDate || startDate;
  const currentEnd = value?.endDate || endDate;

  const [isOpen, setIsOpen] = useState(false);
  const [tempStart, setTempStart] = useState(currentStart);
  const [tempEnd, setTempEnd] = useState(currentEnd);

  useEffect(() => {
    setTempStart(currentStart);
    setTempEnd(currentEnd);
  }, [currentStart, currentEnd]);

  const handleApply = () => {
    if (onChange) {
      (onChange as (range: DateRange) => void)({ startDate: tempStart, endDate: tempEnd });
    }
    setIsOpen(false);
  };

  const handlePresetSelect = (preset: DateRangePreset) => {
    setTempStart(preset.startDate);
    setTempEnd(preset.endDate);
    if (onChange) {
      (onChange as (range: DateRange) => void)({
        startDate: preset.startDate,
        endDate: preset.endDate,
      });
    }
    setIsOpen(false);
  };

  return (
    <div className={cn('relative inline-block', className)}>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        icon={<Calendar className="h-3.5 w-3.5 text-text-muted" />}
        className="h-9 gap-2 font-mono text-xs"
      >
        <span>{currentStart}</span>
        <ChevronRight className="h-3 w-3 text-text-subtle" />
        <span>{currentEnd}</span>
      </Button>

      {isOpen && (
        <div
          role="dialog"
          aria-label="Select Date Range"
          className="animate-fade-in absolute left-0 z-40 mt-1.5 w-80 rounded-card border border-border bg-surface-card p-4 font-sans text-xs shadow-elevated"
        >
          <div className="space-y-3">
            <div className="font-mono text-[11px] text-text-muted">Preset Windows</div>
            <div className="flex flex-wrap gap-1.5">
              {presets.map((p) => (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => handlePresetSelect(p)}
                  className="transition-standard rounded-chip border border-border px-2 py-1 font-mono text-[11px] hover:bg-surface-subtle"
                >
                  {p.label}
                </button>
              ))}
            </div>

            <div className="border-border/60 space-y-2 border-t pt-2 font-mono">
              <div>
                <label className="mb-0.5 block text-[10px] text-text-muted">
                  Start Date (UTC+5:30)
                </label>
                <input
                  type="date"
                  value={tempStart}
                  onChange={(e) => setTempStart(e.target.value)}
                  className="w-full rounded border border-border bg-surface-white px-2 py-1 text-xs focus:ring-accent"
                />
              </div>

              <div>
                <label className="mb-0.5 block text-[10px] text-text-muted">
                  End Date (UTC+5:30)
                </label>
                <input
                  type="date"
                  value={tempEnd}
                  onChange={(e) => setTempEnd(e.target.value)}
                  className="w-full rounded border border-border bg-surface-white px-2 py-1 text-xs focus:ring-accent"
                />
              </div>
            </div>

            <div className="border-border/60 flex items-center justify-end gap-2 border-t pt-2">
              <Button variant="ghost" size="sm" onClick={() => setIsOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleApply}>
                Apply Range
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
