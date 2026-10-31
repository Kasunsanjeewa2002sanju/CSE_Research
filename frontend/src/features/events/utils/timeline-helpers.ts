import type { PoliticalEvent } from '@/api/types';

export interface TimelineGroup {
  category: string;
  color: string;
  badgeBg: string;
  events: PoliticalEvent[];
}

/**
 * Election type color palette conforming strictly to blue family + accent (Rule FR1).
 * Never red or green.
 */
export const EVENT_TYPE_COLORS: Record<string, { primary: string; light: string; border: string }> =
  {
    Presidential: {
      primary: '#0A2A66', // Deep navy
      light: '#EEF4FF',
      border: '#C9DBFA',
    },
    Parliamentary: {
      primary: '#1246B3', // Cobalt blue
      light: '#F0F5FF',
      border: '#B3CCFF',
    },
    Provincial: {
      primary: '#0095B3', // Cyan accent
      light: '#E6F8FA',
      border: '#99E3ED',
    },
    Crisis: {
      primary: '#53627A', // Slate neutral
      light: '#F6F8FC',
      border: '#E1E8F2',
    },
    Policy: {
      primary: '#1B5CD6', // Bright primary blue
      light: '#EFF6FF',
      border: '#BFDBFE',
    },
  };

export function getEventTypeColor(category: string): {
  primary: string;
  light: string;
  border: string;
} {
  return (
    EVENT_TYPE_COLORS[category] ?? {
      primary: '#1246B3',
      light: '#F0F5FF',
      border: '#B3CCFF',
    }
  );
}

/**
 * Groups events by election category.
 */
export function groupEventsByCategory(events: PoliticalEvent[]): TimelineGroup[] {
  const groups: Record<string, PoliticalEvent[]> = {};

  for (const event of events) {
    const cat = event.category || 'Parliamentary';
    if (!groups[cat]) {
      groups[cat] = [];
    }
    groups[cat].push(event);
  }

  // Sort within each category by date ascending
  for (const cat in groups) {
    groups[cat].sort((a, b) => (a.date > b.date ? 1 : -1));
  }

  const preferredOrder = ['Presidential', 'Parliamentary', 'Provincial', 'Crisis', 'Policy'];
  const result: TimelineGroup[] = [];

  for (const cat of preferredOrder) {
    if (groups[cat] && groups[cat].length > 0) {
      const palette = getEventTypeColor(cat);
      result.push({
        category: cat,
        color: palette.primary,
        badgeBg: palette.light,
        events: groups[cat],
      });
    }
  }

  return result;
}

/**
 * Calculates start and end year bounds for timeline scale.
 */
export function getTimelineBounds(events: PoliticalEvent[]): { minYear: number; maxYear: number } {
  if (events.length === 0) {
    return { minYear: 2000, maxYear: 2024 };
  }

  let min = 9999;
  let max = 0;

  for (const e of events) {
    if (e.date && e.date.length >= 4) {
      const y = parseInt(e.date.slice(0, 4), 10);
      if (!isNaN(y)) {
        if (y < min) min = y;
        if (y > max) max = y;
      }
    }
  }

  return {
    minYear: min === 9999 ? 2000 : min,
    maxYear: max === 0 ? 2024 : max,
  };
}

/**
 * Computes horizontal percentage offset (0% to 100%) for a given date.
 */
export function calculateDateOffset(dateStr: string, minYear: number, maxYear: number): number {
  if (!dateStr || dateStr.length < 4) return 0;
  const year = parseInt(dateStr.slice(0, 4), 10);
  const month = dateStr.length >= 7 ? parseInt(dateStr.slice(5, 7), 10) - 1 : 0;
  const day = dateStr.length >= 10 ? parseInt(dateStr.slice(8, 10), 10) : 1;

  const totalYears = Math.max(1, maxYear - minYear + 1);
  const yearFraction = year - minYear + month / 12 + day / 365;
  const pct = (yearFraction / totalYears) * 100;
  return Math.max(0, Math.min(100, pct));
}
