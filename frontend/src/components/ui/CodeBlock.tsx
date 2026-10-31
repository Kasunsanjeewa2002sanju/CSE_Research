import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { IconButton } from './IconButton';
import { cn } from '@/lib/utils';

export interface CodeBlockProps {
  code: string;
  language?: string;
  title?: string;
  maxHeight?: string;
  className?: string;
}

export function CodeBlock({
  code,
  language = 'json',
  title,
  maxHeight = '280px',
  className,
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore
    }
  };

  return (
    <div
      className={cn(
        'overflow-hidden rounded-card border border-border bg-surface-subtle font-mono text-xs shadow-soft',
        className
      )}
    >
      <div className="border-border/60 flex items-center justify-between border-b bg-surface-card px-4 py-2">
        <div className="flex items-center gap-2 text-text-muted">
          <span className="text-[10px] font-bold uppercase tracking-wider text-accent-hover">
            {language}
          </span>
          {title && <span className="font-semibold text-text-primary">{title}</span>}
        </div>
        <IconButton
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          aria-label={copied ? 'Copied to clipboard' : 'Copy code to clipboard'}
        >
          {copied ? (
            <Check className="h-3.5 w-3.5 text-data-up" />
          ) : (
            <Copy className="h-3.5 w-3.5 text-text-muted" />
          )}
        </IconButton>
      </div>

      <pre
        style={{ maxHeight }}
        className="overflow-x-auto bg-surface-subtle p-4 text-[11px] leading-relaxed text-text-primary"
      >
        <code>{code}</code>
      </pre>
    </div>
  );
}

export interface JsonViewerProps {
  data: unknown;
  title?: string;
  className?: string;
}

export function JsonViewer({ data, title = 'JSON Payload', className }: JsonViewerProps) {
  const formatted = JSON.stringify(data, null, 2);
  return <CodeBlock code={formatted} language="json" title={title} className={className} />;
}
