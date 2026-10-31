import { useEffect, useRef, useState } from 'react';

export type TickDirection = 'up' | 'down' | null;

/**
 * Hook providing subtle, brief highlight animation on value update.
 * Respects prefers-reduced-motion (no layout shift, reserves width with tabular-nums).
 */
export function useTickAnimation(value: number | string | null | undefined): {
  direction: TickDirection;
  flashClassName: string;
} {
  const prevRef = useRef<number | null>(null);
  const [direction, setDirection] = useState<TickDirection>(null);

  useEffect(() => {
    if (value === null || value === undefined) return;
    const num =
      typeof value === 'string' ? parseFloat(value.replace(/[^0-9.-]/g, '')) : Number(value);
    if (isNaN(num)) return;

    if (prevRef.current !== null && prevRef.current !== num) {
      const dir: TickDirection = num > prevRef.current ? 'up' : 'down';
      setDirection(dir);

      const timer = setTimeout(() => {
        setDirection(null);
      }, 1200);

      prevRef.current = num;
      return () => clearTimeout(timer);
    }

    prevRef.current = num;
  }, [value]);

  let flashClassName = '';
  if (direction === 'up') {
    flashClassName =
      'motion-safe:transition-all motion-safe:duration-500 rounded px-1 -mx-1 bg-emerald-500/15 text-emerald-600 dark:text-emerald-400';
  } else if (direction === 'down') {
    flashClassName =
      'motion-safe:transition-all motion-safe:duration-500 rounded px-1 -mx-1 bg-rose-500/15 text-rose-600 dark:text-rose-400';
  }

  return { direction, flashClassName };
}

/**
 * Throttles sparkline array updates to at most once per `throttleMs` (default 1000ms),
 * preventing unnecessary SVG redraws during high-frequency live ticks.
 */
export function useThrottledSparkline(points: number[], throttleMs = 1000): number[] {
  const [throttled, setThrottled] = useState<number[]>(points);
  const lastUpdateRef = useRef<number>(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const now = Date.now();
    const elapsed = now - lastUpdateRef.current;

    if (elapsed >= throttleMs) {
      lastUpdateRef.current = now;
      setThrottled(points);
    } else {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        lastUpdateRef.current = Date.now();
        setThrottled(points);
      }, throttleMs - elapsed);
    }

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [points, throttleMs]);

  return throttled;
}
