/**
 * Econometric & UI Data Formatters (Stage 5 Enhanced)
 *
 * Formats values strictly provided by the backend API.
 * Never invents or hardcodes data.
 * All formatting utilizes tabular numerals styling and Asia/Colombo timezone.
 */

export function formatNumber(value: number | null | undefined, decimals = 2): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '—';
  }
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatPercent(
  value: number | null | undefined,
  decimals = 2,
  showSign = false,
  isRawPercent = false
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '—';
  }
  const numericValue = isRawPercent ? value : value * 100;
  const formatted = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(numericValue);

  if (showSign && numericValue > 0) {
    return `+${formatted}%`;
  }
  return `${formatted}%`;
}

/**
 * Formats equity turnover into auto-scaled LKR values (B/M/K).
 * Never returns blank or NaN.
 *
 * Examples:
 * - 9_309_760_000 -> "LKR 9.31B"
 * - 2_840_000_000 -> "LKR 2.84B"
 * - 45_000_000 -> "LKR 45.00M"
 * - 500_000 -> "LKR 500.00K"
 * - 250 -> "LKR 250.00"
 */
export function formatLKR(value: number | null | undefined, decimals = 2): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '—';
  }
  const abs = Math.abs(value);
  const sign = value < 0 ? '-' : '';

  if (abs >= 1e9) {
    return `${sign}LKR ${(abs / 1e9).toFixed(decimals)}B`;
  }
  if (abs >= 1e6) {
    return `${sign}LKR ${(abs / 1e6).toFixed(decimals)}M`;
  }
  if (abs >= 1e3) {
    return `${sign}LKR ${(abs / 1e3).toFixed(decimals)}K`;
  }
  return `${sign}LKR ${abs.toFixed(decimals)}`;
}

/**
 * Formats trading volume into auto-scaled shares counts (M/K).
 * Never returns blank or NaN.
 *
 * Examples:
 * - 245_620_000 -> "245.6M"
 * - 85_400_000 -> "85.4M"
 * - 750_000 -> "750.0K"
 * - 500 -> "500"
 */
export function formatVolume(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '—';
  }
  const abs = Math.abs(value);
  const sign = value < 0 ? '-' : '';

  if (abs >= 1e6) {
    return `${sign}${(abs / 1e6).toFixed(decimals)}M`;
  }
  if (abs >= 1e3) {
    return `${sign}${(abs / 1e3).toFixed(decimals)}K`;
  }
  return `${sign}${Math.round(abs).toLocaleString('en-US')}`;
}

export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return '—';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(d);
  } catch {
    return dateString;
  }
}

/**
 * Formats date strictly in Asia/Colombo timezone.
 * Example: "20 Oct 2026"
 */
export function formatDateColombo(dateInput: string | Date | null | undefined): string {
  if (!dateInput) return '—';
  try {
    const d = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
    if (isNaN(d.getTime())) return String(dateInput);
    return new Intl.DateTimeFormat('en-GB', {
      timeZone: 'Asia/Colombo',
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    }).format(d);
  } catch {
    return String(dateInput);
  }
}

/**
 * Formats date and time strictly in Asia/Colombo timezone.
 * Example: "20 Oct 2026, 16:01:28 Asia/Colombo" or "20 Oct 2026, 04:01 PM"
 */
export function formatDateTimeColombo(
  dateInput: string | Date | null | undefined,
  includeSeconds = true,
  includeTzSuffix = false
): string {
  if (!dateInput) return '—';
  try {
    const d = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
    if (isNaN(d.getTime())) return String(dateInput);
    const formatted = new Intl.DateTimeFormat('en-GB', {
      timeZone: 'Asia/Colombo',
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: includeSeconds ? '2-digit' : undefined,
      hour12: true,
    }).format(d);

    return includeTzSuffix ? `${formatted} Asia/Colombo` : formatted;
  } catch {
    return String(dateInput);
  }
}

export function formatSampleSize(n: number | null | undefined): string {
  if (n === null || n === undefined) return 'n = —';
  return `n = ${n.toLocaleString('en-US')}`;
}

export function formatPValue(p: number | null | undefined): string {
  if (p === null || p === undefined || isNaN(p)) return 'p = —';
  if (p < 0.001) return 'p < 0.001';
  return `p = ${p.toFixed(3)}`;
}

export function formatConfidenceInterval(
  lower: number | null | undefined,
  upper: number | null | undefined,
  decimals = 2
): string {
  if (lower === null || lower === undefined || upper === null || upper === undefined) {
    return '[—, —]';
  }
  return `[${formatPercent(lower, decimals, true)}, ${formatPercent(upper, decimals, true)}]`;
}
