import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

export interface ToastOptions {
  title: string;
  description?: string;
  message?: string;
  variant?: ToastType;
  type?: ToastType;
  duration?: number;
}

interface ToastContextValue {
  showToast: (toast: Omit<ToastMessage, 'id'>) => void;
  toast: (options: ToastOptions) => void;
  dismissToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within a ToastProvider');
  return context;
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (toastItem: Omit<ToastMessage, 'id'>) => {
      const id = Math.random().toString(36).substring(2, 9);
      const newToast: ToastMessage = { ...toastItem, id };
      setToasts((prev) => [...prev, newToast]);

      const duration = toastItem.duration ?? 4500;
      if (duration > 0) {
        setTimeout(() => dismissToast(id), duration);
      }
    },
    [dismissToast]
  );

  const toast = useCallback(
    (options: ToastOptions) => {
      showToast({
        title: options.title,
        message: options.description || options.message,
        type: options.variant || options.type || 'info',
        duration: options.duration,
      });
    },
    [showToast]
  );

  return (
    <ToastContext.Provider value={{ showToast, toast, dismissToast }}>
      {children}
      <div
        aria-live="assertive"
        className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className={cn(
              'animate-fade-in pointer-events-auto flex items-start gap-3 rounded-card border bg-surface-card p-3.5 font-sans text-xs text-text-primary shadow-elevated',
              t.type === 'success' && 'border-data-up/40',
              t.type === 'error' && 'border-data-down/40',
              t.type === 'warning' && 'border-data-warning/40',
              t.type === 'info' && 'border-blue-cobalt/40'
            )}
          >
            <div className="mt-0.5 shrink-0">
              {t.type === 'success' && (
                <CheckCircle2 className="h-4 w-4 text-data-up" aria-hidden="true" />
              )}
              {t.type === 'error' && (
                <AlertCircle className="h-4 w-4 text-data-down" aria-hidden="true" />
              )}
              {t.type === 'warning' && (
                <AlertTriangle className="h-4 w-4 text-data-warning" aria-hidden="true" />
              )}
              {t.type === 'info' && (
                <Info className="h-4 w-4 text-blue-vibrant" aria-hidden="true" />
              )}
            </div>

            <div className="flex-1 space-y-0.5">
              <div className="font-heading font-semibold text-text-primary">{t.title}</div>
              {t.message && <p className="leading-relaxed text-text-muted">{t.message}</p>}
            </div>

            <button
              type="button"
              onClick={() => dismissToast(t.id)}
              aria-label="Dismiss notification"
              className="p-0.5 text-text-subtle hover:text-text-primary"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
