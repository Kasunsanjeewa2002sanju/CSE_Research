import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { formatDateTimeColombo } from '@/utils/formatters';
import {
  newsItemSchema,
  newsItemsResponseSchema,
  newsFeedsResponseSchema,
  pipelineStatsResponseSchema,
} from '@/api/zod-schemas';
import type {
  NewsItem,
  NewsFeedItem,
  PipelineStatsResponse,
} from '@/features/news/types';
import { NewsCard } from '@/features/news/components/NewsCard';
import { NewsDetailDrawer } from '@/features/news/components/NewsDetailDrawer';
import { FeedHealthTable } from '@/features/news/components/FeedHealthTable';
import { RelevanceFunnel } from '@/features/news/components/RelevanceFunnel';
import { RunHistoryTable } from '@/features/news/components/RunHistoryTable';
import { FailuresLog } from '@/features/news/components/FailuresLog';

describe('Stage F8: News Feed & Pipeline Monitor Unit Tests', () => {
  const mockNewsItem: NewsItem = {
    id: 'test_item_001',
    title: 'Central Bank of Sri Lanka Holds Policy Rates Steady Ahead of Election',
    headline: 'Central Bank of Sri Lanka Holds Policy Rates Steady Ahead of Election',
    description: 'The Monetary Board of the CBSL decided to maintain the Standing Deposit Facility Rate at 8.25%.',
    published_at: '2026-10-13T06:43:50.000Z',
    source: 'Ada Derana',
    url: 'https://adaderana.lk/news/test_item_001',
    image_url: null,
    sentiment_score: 0.85,
    tags: ['Economic Policy', 'Positive'],
    category: 'economic_policy',
    stage: 'pre_announcement',
    direction: 'positive',
    confidence: 0.92,
    language: 'en',
    is_relevant: true,
    evidence_strength: 'strong',
    reason: 'Interest rate stability provides macroeconomic certainty supporting Colombo equities sentiment.',
    entities: ['Central Bank of Sri Lanka', 'CBSL', 'Monetary Board'],
    affected_sectors: ['Banking', 'Diversified Financials'],
    duplicate_cluster: [
      {
        id: 'dup_item_002',
        headline: 'CBSL maintains policy rates steady as inflation remains subdued',
        source: 'The Island',
        url: 'https://island.lk/news/dup_002',
        published_at: '2026-10-13T07:15:00.000Z',
      },
    ],
    diff_h1: 14.5,
    diff_h5: 38.2,
    prob_up_h1: 0.78,
    prob_up_h5: 0.82,
  };

  const mockFeeds: NewsFeedItem[] = [
    {
      id: 'feed_1',
      name: 'Ada Derana',
      url: 'http://www.adaderana.lk/rss.php',
      status: 'active',
      status_code: 200,
      is_active: true,
      last_polled_at: '2026-10-16T17:59:23Z',
      article_count_24h: 25,
      response_time_sec: 0.652,
      error_count: 0,
      last_error: null,
      feed_type: 'rss',
    },
    {
      id: 'feed_2',
      name: 'Daily Mirror',
      url: 'https://www.dailymirror.lk/rss/breaking-news',
      status: 'degraded',
      status_code: 200,
      is_active: false,
      last_polled_at: '2026-10-16T17:59:28Z',
      article_count_24h: 0,
      response_time_sec: 0.292,
      error_count: 1,
      last_error: 'No RSS entries parsed (empty feed or HTML returned)',
      feed_type: 'rss',
    },
    {
      id: 'feed_3',
      name: 'Newsfirst',
      url: 'https://www.newsfirst.lk/feed/',
      status: 'error',
      status_code: 403,
      is_active: false,
      last_polled_at: '2026-10-16T17:59:29Z',
      article_count_24h: 0,
      response_time_sec: 0.19,
      error_count: 1,
      last_error: 'HTTP 403',
      feed_type: 'rss',
    },
  ];

  const mockPipelineStats: PipelineStatsResponse = {
    summary: {
      total_ingested_items: 162,
      relevant_items: 42,
      active_feeds: 8,
      degraded_feeds: 2,
      error_feeds: 4,
      total_feeds: 14,
      last_ingested_at: '2026-10-16T17:59:23Z',
      sources_count: 6,
    },
    feed_health: {
      total: 14,
      active: 8,
      degraded: 2,
      error: 4,
    },
    items_per_hour_by_source: [
      {
        hour: '17:00',
        total: 15,
        by_source: { 'Ada Derana': 10, 'The Island': 5 },
      },
    ],
    classification_distribution: [
      { category: 'political', label: 'Political', count: 70, percentage: 43.2 },
      { category: 'economic', label: 'Economic', count: 50, percentage: 30.9 },
    ],
    relevance_funnel: {
      stages: [
        { stage: 'fetched', label: 'Raw Fetched', count: 248, percentage: 100.0, description: 'Raw RSS items' },
        { stage: 'deduplicated', label: 'Deduplicated', count: 162, percentage: 65.3, description: 'Similarity >0.85' },
        { stage: 'relevant', label: 'Macro Relevant', count: 42, percentage: 25.9, description: 'Stage 10 classifier' },
        { stage: 'predicted', label: 'Scenario Forecast', count: 42, percentage: 100.0, description: 'Stage 11 engine' },
      ],
      conversion_rate_pct: 16.9,
      deduplication_rate_pct: 34.7,
    },
    language_split: [
      { language: 'en', label: 'English', count: 150, percentage: 92.6 },
      { language: 'si', label: 'Sinhala', count: 12, percentage: 7.4 },
    ],
    run_history: [
      {
        run_id: 'run_20261016_175923',
        started_at: '2026-10-16T17:58:42Z',
        completed_at: '2026-10-16T17:59:31Z',
        status: 'completed',
        articles_ingested: 11,
        duration_sec: 48.2,
      },
    ],
    failures_log: [
      {
        feed_name: 'Newsfirst',
        url: 'https://www.newsfirst.lk/feed/',
        status: 'error',
        status_code: 403,
        error_message: 'HTTP 403',
        last_checked: '2026-10-16T17:59:29Z',
        severity: 'critical',
      },
    ],
  };

  describe('1. Formatter: formatDateTimeColombo', () => {
    it('formats UTC ISO timestamp into Asia/Colombo (+05:30) timezone', () => {
      // 2026-10-13T06:43:50Z + 05:30 = 2026-10-13 12:13:50
      const formatted = formatDateTimeColombo('2026-10-13T06:43:50.000Z');
      expect(formatted).toContain('13 Oct 2026');
      expect(formatted).toContain('12:13');
    });

    it('returns fallback dash for null or undefined input', () => {
      expect(formatDateTimeColombo(null)).toBe('—');
      expect(formatDateTimeColombo(undefined)).toBe('—');
    });
  });

  describe('2. Zod Boundary Schemas', () => {
    it('validates a complete NewsItem with duplicate cluster and classifier telemetry', () => {
      const parsed = newsItemSchema.parse(mockNewsItem);
      expect(parsed.id).toBe('test_item_001');
      expect(parsed.direction).toBe('positive');
      expect(parsed.confidence).toBe(0.92);
      expect(parsed.duplicate_cluster).toHaveLength(1);
    });

    it('validates paginated news items response schema', () => {
      const parsed = newsItemsResponseSchema.parse({
        items: [mockNewsItem],
        total: 1,
        count: 1,
        page: 1,
        page_size: 24,
        total_pages: 1,
        has_next: false,
        filters: {
          sources: ['Ada Derana', 'The Island'],
          categories: ['economic_policy'],
          stages: ['pre_announcement'],
          languages: ['en'],
          evidence_strengths: ['all', 'strong'],
          relevance_options: ['all', 'relevant', 'not_relevant'],
        },
      });
      expect(parsed.total).toBe(1);
      expect(parsed.items[0].headline).toBe(mockNewsItem.headline);
    });

    it('validates news feed health schema with active, degraded, and error statuses', () => {
      const parsed = newsFeedsResponseSchema.parse({ feeds: mockFeeds });
      expect(parsed.feeds).toHaveLength(3);
      expect(parsed.feeds[1].status).toBe('degraded');
      expect(parsed.feeds[2].status).toBe('error');
    });

    it('validates complete pipeline stats response schema', () => {
      const parsed = pipelineStatsResponseSchema.parse(mockPipelineStats);
      expect(parsed.summary.total_ingested_items).toBe(162);
      expect(parsed.relevance_funnel.stages).toHaveLength(4);
      expect(parsed.failures_log).toHaveLength(1);
    });
  });

  describe('3. NewsCard Component', () => {
    it('renders headline, source, Colombo timestamp, chips, and confidence', () => {
      const onSelect = vi.fn();
      render(
        <BrowserRouter>
          <NewsCard item={mockNewsItem} onSelect={onSelect} />
        </BrowserRouter>
      );

      // Headline
      expect(screen.getByText(mockNewsItem.headline!)).toBeInTheDocument();
      // Source
      expect(screen.getByText('Ada Derana')).toBeInTheDocument();
      // Confidence
      expect(screen.getByText('92%')).toBeInTheDocument();
      // Direction
      expect(screen.getByText('positive')).toBeInTheDocument();
      // Category chip
      expect(screen.getByText('economic policy')).toBeInTheDocument();
      // Stage chip
      expect(screen.getByText('pre announcement')).toBeInTheDocument();
      // Buttons
      const readBtn = screen.getByRole('link', { name: /read article/i });
      expect(readBtn).toHaveAttribute('href', mockNewsItem.url);
      expect(readBtn).toHaveAttribute('target', '_blank');
      expect(readBtn).toHaveAttribute('rel', 'noopener noreferrer');

      const predictBtn = screen.getByRole('link', { name: /predict impact/i });
      expect(predictBtn).toHaveAttribute('href', `/predictor?news=${mockNewsItem.id}`);
    });

    it('shows category icon when no image_url is provided (no stock photos)', () => {
      const { container } = render(
        <BrowserRouter>
          <NewsCard item={{ ...mockNewsItem, image_url: null }} onSelect={vi.fn()} />
        </BrowserRouter>
      );
      // No <img> tag rendered
      expect(container.querySelector('img')).toBeNull();
      // Category icon container exists
      expect(container.querySelector('.text-blue-cobalt')).toBeInTheDocument();
    });

    it('renders thumbnail when image_url is provided by API', () => {
      const { container } = render(
        <BrowserRouter>
          <NewsCard
            item={{ ...mockNewsItem, image_url: 'https://example.com/cbsl.jpg' }}
            onSelect={vi.fn()}
          />
        </BrowserRouter>
      );
      const img = container.querySelector('img');
      expect(img).not.toBeNull();
      expect(img).toHaveAttribute('src', 'https://example.com/cbsl.jpg');
    });

    it('triggers onSelect when headline is clicked', () => {
      const onSelect = vi.fn();
      render(
        <BrowserRouter>
          <NewsCard item={mockNewsItem} onSelect={onSelect} />
        </BrowserRouter>
      );
      fireEvent.click(screen.getByText(mockNewsItem.headline!));
      expect(onSelect).toHaveBeenCalledWith(mockNewsItem);
    });
  });

  describe('4. NewsDetailDrawer Component', () => {
    it('renders structured classification, reason text, entities, and duplicate cluster', () => {
      const onClose = vi.fn();
      render(
        <BrowserRouter>
          <NewsDetailDrawer item={mockNewsItem} onClose={onClose} />
        </BrowserRouter>
      );

      // Classification header
      expect(screen.getByText('Article Intelligence & Classification')).toBeInTheDocument();
      // Reason text
      expect(screen.getByText(mockNewsItem.reason!)).toBeInTheDocument();
      // Entities
      expect(screen.getByText('Central Bank of Sri Lanka')).toBeInTheDocument();
      expect(screen.getByText('CBSL')).toBeInTheDocument();
      // Sectors
      expect(screen.getByText('Banking')).toBeInTheDocument();
      // Duplicate Cluster
      expect(screen.getByText(/Duplicate Story Cluster \(1\)/i)).toBeInTheDocument();
      expect(
        screen.getByText('CBSL maintains policy rates steady as inflation remains subdued')
      ).toBeInTheDocument();
      expect(screen.getByText('The Island')).toBeInTheDocument();
    });
  });

  describe('5. FeedHealthTable Component', () => {
    it('clearly marks active, degraded, and error feeds with warnings', () => {
      render(<FeedHealthTable feeds={mockFeeds} />);

      // Warning banner for degraded/failing feeds
      expect(screen.getByText(/2 Feed Sources Require Attention/i)).toBeInTheDocument();
      // Feed names
      expect(screen.getByText('Ada Derana')).toBeInTheDocument();
      expect(screen.getByText('Daily Mirror')).toBeInTheDocument();
      expect(screen.getByText('Newsfirst')).toBeInTheDocument();
      // HTTP codes
      expect(screen.getByText('403')).toBeInTheDocument();
      // Error message
      expect(screen.getByText('HTTP 403')).toBeInTheDocument();
    });
  });

  describe('6. RelevanceFunnel Component', () => {
    it('renders all 4 pipeline stages with retention percentages', () => {
      render(<RelevanceFunnel funnel={mockPipelineStats.relevance_funnel} />);

      expect(screen.getByText('Raw Fetched')).toBeInTheDocument();
      expect(screen.getByText('Deduplicated')).toBeInTheDocument();
      expect(screen.getByText('Macro Relevant')).toBeInTheDocument();
      expect(screen.getByText('Scenario Forecast')).toBeInTheDocument();
      expect(screen.getByText('16.9%')).toBeInTheDocument();
    });
  });

  describe('7. RunHistoryTable Component', () => {
    it('renders daemon run IDs, durations, and ingested article counts', () => {
      render(<RunHistoryTable runs={mockPipelineStats.run_history} />);

      expect(screen.getByText('run_20261016_175923')).toBeInTheDocument();
      expect(screen.getByText('48.2s')).toBeInTheDocument();
      expect(screen.getByText('11')).toBeInTheDocument();
    });
  });

  describe('8. FailuresLog Component', () => {
    it('displays network failure diagnostics with HTTP codes and causes', () => {
      render(<FailuresLog failures={mockPipelineStats.failures_log} />);

      expect(screen.getByText('Newsfirst')).toBeInTheDocument();
      expect(screen.getAllByText(/HTTP 403/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/Cloudflare WAF \/ anti-bot challenge/i)).toBeInTheDocument();
    });
  });
});
