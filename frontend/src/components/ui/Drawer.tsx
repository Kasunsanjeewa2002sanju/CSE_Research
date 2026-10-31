import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { IconButton } from './IconButton';
import { cn } from '@/lib/utils';

export interface DrawerProps {
  isOpen?: boolean;
  open?: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  side?: 'left' | 'right';
  position?: 'left' | 'right';
  className?: string;
}

export function Drawer({
  isOpen,
  open,
  onClose,
  title,
  description,
  children,
  side,
  position,
  className,
}: DrawerProps) {
  const visible = open !== undefined ? open : !!isOpen;
  const effectiveSide = position || side || 'right';

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && visible) {
        onClose();
      }
    }
    if (visible) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [visible, onClose]);

  if (!visible) return null;

  return (
    <div role="presentation" className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="bg-blue-navy/40 backdrop-blur-xs animate-fade-in fixed inset-0 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer Panel */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cn(
          'animate-fade-in fixed inset-y-0 z-50 flex w-80 max-w-full flex-col border-border bg-surface-card shadow-elevated transition-transform sm:w-96',
          effectiveSide === 'right' ? 'right-0 border-l' : 'left-0 border-r',
          className
        )}
      >
        <div className="border-border/60 flex items-center justify-between border-b px-5 py-4">
          <div>
            <h3 className="font-heading text-base font-bold text-text-primary">{title}</h3>
            {description && (
              <p className="mt-0.5 text-[11px] leading-relaxed text-text-muted">{description}</p>
            )}
          </div>
          <IconButton variant="ghost" size="sm" onClick={onClose} aria-label="Close drawer">
            <X className="h-4 w-4" />
          </IconButton>
        </div>

        <div className="flex-1 overflow-y-auto p-5 font-sans text-xs">{children}</div>
      </div>
    </div>
  );
}
