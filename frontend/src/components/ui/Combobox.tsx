import { useState, useRef, useEffect } from 'react';
import { Search, ChevronDown, Check, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ComboboxOption {
  value: string;
  label: string;
  category?: string;
}

export interface ComboboxProps {
  options: ComboboxOption[];
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  disabled?: boolean;
  className?: string;
}

export function Combobox({
  options,
  value,
  onChange,
  placeholder = 'Select option...',
  label,
  disabled = false,
  className,
}: ComboboxProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find((o) => o.value === value);

  const filteredOptions = options.filter(
    (o) =>
      o.label.toLowerCase().includes(search.toLowerCase()) ||
      (o.category && o.category.toLowerCase().includes(search.toLowerCase()))
  );

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className={cn('relative w-full space-y-1.5', className)}>
      {label && (
        <label className="block font-sans text-xs font-medium text-text-primary">{label}</label>
      )}

      <div
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className={cn(
          'transition-standard flex w-full cursor-pointer items-center justify-between rounded-button border border-border bg-surface-white px-3 py-2 font-sans text-xs text-text-primary shadow-soft focus-within:ring-2 focus-within:ring-accent',
          disabled && 'pointer-events-none cursor-not-allowed opacity-50'
        )}
      >
        <span className={cn('truncate', !selectedOption && 'text-text-muted')}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <div className="flex items-center gap-1 text-text-muted">
          {selectedOption && (
            <button
              type="button"
              aria-label="Clear selection"
              onClick={(e) => {
                e.stopPropagation();
                onChange('');
              }}
              className="p-0.5 hover:text-text-primary"
            >
              <X className="h-3 w-3" />
            </button>
          )}
          <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
        </div>
      </div>

      {isOpen && (
        <div
          role="listbox"
          className="animate-fade-in absolute z-50 mt-1 max-h-60 w-full overflow-y-auto rounded-card border border-border bg-surface-card p-1 shadow-card"
        >
          <div className="border-border/60 mb-1 flex items-center gap-2 border-b px-2 py-1.5">
            <Search className="h-3.5 w-3.5 shrink-0 text-text-muted" aria-hidden="true" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search..."
              autoFocus
              className="w-full bg-transparent font-sans text-xs text-text-primary focus:outline-none"
            />
          </div>

          {filteredOptions.length === 0 ? (
            <div className="px-3 py-3 text-center text-xs text-text-muted">No matches found.</div>
          ) : (
            filteredOptions.map((opt) => {
              const isSelected = opt.value === value;
              return (
                <div
                  key={opt.value}
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => {
                    onChange(opt.value);
                    setIsOpen(false);
                    setSearch('');
                  }}
                  className={cn(
                    'transition-standard flex cursor-pointer items-center justify-between rounded-button px-2.5 py-1.5 font-sans text-xs',
                    isSelected
                      ? 'dark:bg-blue-soft/30 bg-blue-ice font-semibold text-blue-navy dark:text-blue-vibrant'
                      : 'text-text-primary hover:bg-surface-subtle'
                  )}
                >
                  <div className="flex flex-col">
                    <span>{opt.label}</span>
                    {opt.category && (
                      <span className="font-mono text-[10px] text-text-muted">{opt.category}</span>
                    )}
                  </div>
                  {isSelected && (
                    <Check className="h-3.5 w-3.5 text-blue-cobalt" aria-hidden="true" />
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
