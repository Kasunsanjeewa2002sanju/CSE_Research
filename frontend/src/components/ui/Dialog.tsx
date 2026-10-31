import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { IconButton } from './IconButton';
import { cn } from '@/lib/utils';

export interface DialogProps {
  isOpen?: boolean;
  open?: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

export function Dialog({
  isOpen,
  open,
  onClose,
  title,
  description,
  children,
  footer,
  className,
}: DialogProps) {
  const visible = open !== undefined ? open : !!isOpen;
  const dialogRef = useRef<HTMLDivElement>(null);

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
    <div
      role="presentation"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
    >
      {/* Backdrop */}
      <div
        className="bg-blue-navy/40 backdrop-blur-xs animate-fade-in fixed inset-0 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Card */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        className={cn(
          'animate-fade-in relative z-50 w-full max-w-lg rounded-card border border-border bg-surface-card p-6 text-text-primary shadow-elevated',
          className
        )}
      >
        <div className="border-border/60 flex items-start justify-between gap-4 border-b pb-4">
          <div>
            <h3 id="dialog-title" className="font-heading text-lg font-bold text-text-primary">
              {title}
            </h3>
            {description && (
              <p className="mt-1 text-xs leading-relaxed text-text-muted">{description}</p>
            )}
          </div>
          <IconButton variant="ghost" size="sm" onClick={onClose} aria-label="Close dialog">
            <X className="h-4 w-4" />
          </IconButton>
        </div>

        <div className="py-4 font-sans text-xs leading-relaxed">{children}</div>

        {footer && (
          <div className="border-border/60 flex items-center justify-end gap-2 border-t pt-4">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
