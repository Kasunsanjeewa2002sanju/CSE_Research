import { useMemo } from 'react';

export interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  fill?: boolean;
  strokeWidth?: number;
  className?: string;
}

export function Sparkline({
  data,
  width = 96,
  height = 24,
  color = '#1246B3',
  fill = true,
  strokeWidth = 1.5,
  className = '',
}: SparklineProps) {
  const { pathD, areaD } = useMemo(() => {
    if (!data || data.length < 2) {
      return { pathD: '', areaD: '' };
    }

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    // Pad slightly so stroke does not clip
    const pad = 2;
    const effectiveHeight = height - pad * 2;
    const effectiveWidth = width - pad * 2;

    const points = data.map((val, idx) => {
      const x = pad + (idx / (data.length - 1)) * effectiveWidth;
      const y = pad + effectiveHeight - ((val - min) / range) * effectiveHeight;
      return [x, y];
    });

    const pathString = points.reduce((acc, [x, y], idx) => {
      return idx === 0
        ? `M ${x.toFixed(1)} ${y.toFixed(1)}`
        : `${acc} L ${x.toFixed(1)} ${y.toFixed(1)}`;
    }, '');

    const first = points[0];
    const last = points[points.length - 1];
    const areaString = `${pathString} L ${last[0].toFixed(1)} ${height} L ${first[0].toFixed(1)} ${height} Z`;

    return { pathD: pathString, areaD: areaString };
  }, [data, width, height]);

  if (!data || data.length < 2) {
    return <div className="h-6 w-24 rounded bg-surface-subtle" />;
  }

  const gradientId = `spark-grad-${Math.random().toString(36).substring(2, 8)}`;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={`overflow-visible ${className}`}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.25} />
          <stop offset="100%" stopColor={color} stopOpacity={0.0} />
        </linearGradient>
      </defs>
      {fill && <path d={areaD} fill={`url(#${gradientId})`} />}
      <path
        d={pathD}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
