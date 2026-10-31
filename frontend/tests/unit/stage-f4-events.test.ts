import { describe, it, expect } from 'vitest';
import {
  groupEventsByCategory,
  getTimelineBounds,
  calculateDateOffset,
  getEventTypeColor,
  EVENT_TYPE_COLORS,
} from '@/features/events/utils/timeline-helpers';
import { alignAspiPath, createCompareChartOption } from '@/features/events/utils/compare-helpers';
import { politicalEventSchema, eventDetailSchema, eventsCoverageSchema } from '@/api/zod-schemas';
import type { MarketSeriesPoint, PoliticalEvent } from '@/api/types';

describe('Stage F4: Election Events Unit Tests', () => {
  const sampleEvents: PoliticalEvent[] = [
    {
      id: 'ELEC_01',
      date: '2000-10-10',
      event_date: '2000-10-10',
      name: '2000 Sri Lankan Parliamentary Election',
      category: 'Parliamentary',
      current_stage: 'Post-Election Settlement',
      raw_date: '2000-10-10',
      mapped_date: '2000-10-10',
      gap_days: 0,
      sample_period: false,
      is_overlapping: false,
      added_by_researcher: false,
      winner_party: "People's Alliance",
      turnout_pct: 75.6,
      margin_pct: 5.2,
      stages: [
        {
          stage_id: 'announcement',
          stage_name: 'Announcement',
          date: '2000-08-18',
          raw_date: '2000-08-18',
          gap_days: 0,
        },
        {
          stage_id: 'polling',
          stage_name: 'Polling',
          date: '2000-10-10',
          raw_date: '2000-10-10',
          gap_days: 0,
        },
      ],
    },
    {
      id: 'ELEC_06',
      date: '2005-11-17',
      event_date: '2005-11-17',
      name: '2005 Sri Lankan Presidential Election',
      category: 'Presidential',
      current_stage: 'Post-Election Settlement',
      raw_date: '2005-11-17',
      mapped_date: '2005-11-17',
      gap_days: 0,
      sample_period: false,
      is_overlapping: false,
      added_by_researcher: false,
      winner_party: 'UPFA',
      turnout_pct: 73.7,
      margin_pct: 1.8,
      stages: [
        {
          stage_id: 'announcement',
          stage_name: 'Announcement',
          date: '2005-08-22',
          gap_days: 0,
        },
        {
          stage_id: 'polling',
          stage_name: 'Polling',
          date: '2005-11-17',
          gap_days: 0,
        },
      ],
    },
    {
      id: 'ELEC_13',
      date: '2010-01-26',
      event_date: '2010-01-26',
      name: '2010 Sri Lankan Presidential Election',
      category: 'Presidential',
      current_stage: 'Post-Election Settlement',
      raw_date: '2010-01-26',
      mapped_date: '2010-01-26',
      gap_days: 0,
      sample_period: true,
      is_overlapping: false,
      added_by_researcher: false,
      winner_party: 'UPFA',
      turnout_pct: 74.5,
      margin_pct: 17.8,
    },
    {
      id: 'ELEC_04',
      date: '2004-04-26',
      event_date: '2004-04-26',
      name: '2004 North Western Provincial Council Election',
      category: 'Provincial',
      current_stage: 'Post-Election Settlement',
      raw_date: '2004-04-25',
      mapped_date: '2004-04-26',
      gap_days: 1,
      sample_period: false,
      is_overlapping: true,
      added_by_researcher: false,
    },
  ];

  // Synthetic market series covering the 2000 election window
  const sampleSeries: MarketSeriesPoint[] = Array.from({ length: 60 }, (_, i) => {
    // 30 days before 2000-10-10, and 29 days after
    const day = i - 30;
    const baseAspi = 1000;
    // Add small random-like deterministic delta
    const aspi = baseAspi + day * 2 + (day > 0 ? 15 : 0);
    // Rough date string
    const d = new Date(2000, 8, 10 + i);
    const dateStr = d.toISOString().slice(0, 10);
    return {
      date: i === 30 ? '2000-10-10' : dateStr,
      aspi,
      return_pct: 0.002,
    };
  });

  describe('Timeline Helpers & Palette Enforcement', () => {
    it('groups events by category in preferred order', () => {
      const groups = groupEventsByCategory(sampleEvents);
      expect(groups).toHaveLength(3);
      expect(groups[0].category).toBe('Presidential');
      expect(groups[0].events).toHaveLength(2);
      expect(groups[1].category).toBe('Parliamentary');
      expect(groups[1].events).toHaveLength(1);
      expect(groups[2].category).toBe('Provincial');
      expect(groups[2].events).toHaveLength(1);
    });

    it('calculates min and max timeline bounds accurately', () => {
      const bounds = getTimelineBounds(sampleEvents);
      expect(bounds.minYear).toBe(2000);
      expect(bounds.maxYear).toBe(2010);
    });

    it('calculates date offset percentages bounded between 0% and 100%', () => {
      const offset2000 = calculateDateOffset('2000-01-01', 2000, 2010);
      const offset2010 = calculateDateOffset('2010-12-31', 2000, 2010);
      const offsetMid = calculateDateOffset('2005-06-15', 2000, 2010);

      expect(offset2000).toBeGreaterThanOrEqual(0);
      expect(offset2010).toBeLessThanOrEqual(100);
      expect(offsetMid).toBeGreaterThan(40);
      expect(offsetMid).toBeLessThan(60);
    });

    it('enforces Rule FR1: all election type colors use blue family + accent, never red/green', () => {
      const disallowedHex = ['#0F9D6B', '#D93A3A', '#22C55E', '#EF4444', '#DC2626', '#16A34A'];

      for (const [_cat, palette] of Object.entries(EVENT_TYPE_COLORS)) {
        for (const badColor of disallowedHex) {
          expect(palette.primary.toUpperCase()).not.toBe(badColor.toUpperCase());
          expect(palette.light.toUpperCase()).not.toBe(badColor.toUpperCase());
          expect(palette.border.toUpperCase()).not.toBe(badColor.toUpperCase());
        }
      }

      // Check presidential, parliamentary, and provincial mapping
      expect(getEventTypeColor('Presidential').primary).toBe('#0A2A66');
      expect(getEventTypeColor('Parliamentary').primary).toBe('#1246B3');
      expect(getEventTypeColor('Provincial').primary).toBe('#0095B3');
    });
  });

  describe('Event Comparison Path Alignment (Rule FR11)', () => {
    it('aligns ASPI series at reaction date t=0 with 100.0 baseline', () => {
      const event = sampleEvents[0]; // ELEC_01 at 2000-10-10
      const aligned = alignAspiPath(event, sampleSeries, 10);

      expect(aligned).not.toBeNull();
      if (!aligned) return;

      expect(aligned.reactionDate).toBe('2000-10-10');
      expect(aligned.sampleDays).toBeGreaterThan(15);

      const tZero = aligned.points.find((p) => p.relativeDay === 0);
      expect(tZero).toBeDefined();
      expect(tZero?.normalizedLevel).toBe(100);
      expect(tZero?.cumulativeReturnPct).toBe(0);
    });

    it('generates multi-series ECharts compare option with event horizon marker at t=0', () => {
      const aligned1 = alignAspiPath(sampleEvents[0], sampleSeries, 10);
      expect(aligned1).not.toBeNull();
      if (!aligned1) return;

      const option = createCompareChartOption([aligned1]);
      expect(option.xAxis).toBeDefined();
      expect(option.yAxis).toBeDefined();
      expect(option.series).toBeDefined();

      // First series is the event path, second is the markLine horizon
      const seriesList = option.series as unknown[];
      expect(seriesList.length).toBeGreaterThanOrEqual(2);
    });

    it('returns null when series does not cover event date', () => {
      const futureEvent: PoliticalEvent = {
        ...sampleEvents[0],
        date: '2035-01-01',
        mapped_date: '2035-01-01',
      };
      const aligned = alignAspiPath(futureEvent, sampleSeries, 10);
      expect(aligned).toBeNull();
    });
  });

  describe('Zod Schema Boundary Validation', () => {
    it('validates politicalEventSchema with stage mapping and gap days', () => {
      const parsed = politicalEventSchema.parse(sampleEvents[0]);
      expect(parsed.id).toBe('ELEC_01');
      expect(parsed.category).toBe('Parliamentary');
      expect(parsed.gap_days).toBe(0);
    });

    it('validates eventDetailSchema with breakdown stages', () => {
      const parsed = eventDetailSchema.parse(sampleEvents[0]);
      expect(parsed.stages).toHaveLength(2);
      expect(parsed.stages[0].stage_id).toBe('announcement');
    });

    it('validates eventsCoverageSchema with uncovered types', () => {
      const mockCoverage = {
        total_events: 24,
        total_stages: 146,
        years_covered: '2000–2024',
        year_min: 2000,
        year_max: 2024,
        counts_by_type: { Parliamentary: 7, Provincial: 12, Presidential: 5 },
        counts_by_stage: { Announcement: 24, Polling: 24, Result: 24 },
        sample_period_events: 16,
        overlapping_events: 2,
        added_by_researcher_events: 0,
        uncovered_types: [
          { type: 'Crisis', reason: 'Constitutional crises are catalogued separately.' },
          { type: 'Policy', reason: 'Macroeconomic policy shifts evaluated in macro studies.' },
        ],
      };

      const parsed = eventsCoverageSchema.parse(mockCoverage);
      expect(parsed.total_events).toBe(24);
      expect(parsed.uncovered_types).toHaveLength(2);
      expect(parsed.uncovered_types[0].type).toBe('Crisis');
    });
  });
});
