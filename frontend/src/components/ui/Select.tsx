import React from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps extends Omit<
  React.SelectHTMLAttributes<HTMLSelectElement>,
  'onChange'
> {
  label?: string;
  error?: string;
  options: SelectOption[];
  onChange?: (value: string) => void;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, options, id, onChange, ...props }, ref) => {
    const generatedId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      if (!onChange) return;
      // Handle both (value: string) => void and (e: ChangeEvent) => void
      onChange(e.target.value);
    };

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label
            htmlFor={generatedId}
            className="block font-sans text-xs font-medium text-text-primary"
          >
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={generatedId}
            onChange={handleChange}
            className={cn(
              'transition-standard w-full cursor-pointer appearance-none rounded-button border border-border bg-surface-white px-3 py-2 pr-8 font-sans text-xs text-text-primary shadow-soft focus-visible:border-transparent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:pointer-events-none disabled:opacity-50',
              error && 'border-data-down focus-visible:ring-data-down',
              className
            )}
            {...props}
          >
            {options.map((opt) => (
              <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                {opt.label}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2.5 text-text-muted">
            <ChevronDown className="h-4 w-4" aria-hidden="true" />
          </div>
        </div>
        {error && <p className="font-mono text-[11px] text-data-down">{error}</p>}
      </div>
    );
  }
);

Select.displayName = 'Select';
