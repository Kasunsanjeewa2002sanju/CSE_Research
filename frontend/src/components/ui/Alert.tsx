import React from 'react';
import { cn } from '@/lib/utils';
import { AlertCircle, AlertTriangle, CheckCircle2, Info } from 'lucide-react';

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'warning' | 'destructive' | 'success';
  title?: string;
}

export function Alert({ className, variant = 'info', title, children, ...props }: AlertProps) {
  const icons = {
    info: <Info className="text-primary h-5 w-5 shrink-0" aria-hidden="true" />,
    warning: <AlertTriangle className="h-5 w-5 shrink-0 text-amber-500" aria-hidden="true" />,
    destructive: <AlertCircle className="text-destructive h-5 w-5 shrink-0" aria-hidden="true" />,
    success: <CheckCircle2 className="text-market-up h-5 w-5 shrink-0" aria-hidden="true" />,
  };

  const borderStyles = {
    info: 'border-primary/20 bg-primary/5 text-foreground',
    warning: 'border-amber-500/20 bg-amber-500/5 text-foreground',
    destructive: 'border-destructive/20 bg-destructive/5 text-foreground',
    success: 'border-market-up/20 bg-market-up/5 text-foreground',
  };

  return (
    <div
      role="alert"
      className={cn(
        'flex items-start gap-3 rounded-lg border p-4 text-sm',
        borderStyles[variant],
        className
      )}
      {...props}
    >
      {icons[variant]}
      <div className="flex-1 space-y-1">
        {title && (
          <h5 className="font-heading font-semibold leading-none tracking-tight">{title}</h5>
        )}
        <div className="text-sm leading-relaxed opacity-90">{children}</div>
      </div>
    </div>
  );
}
