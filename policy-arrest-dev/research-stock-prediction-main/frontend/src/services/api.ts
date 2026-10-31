import {
  TimelineResponse,
  EventDetail,
  PredictionResult,
  BacktestResult,
  NewsArticleItem,
  VerificationResponse,
  LiveMarketStatus,
  LiveIndices,
  ListedSecurity
} from '../types';

const API_BASE = '/api';

export const api = {
  // Health & Inventory
  getHealth: async () => {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },

  getInventory: async () => {
    const res = await fetch(`${API_BASE}/inventory`);
    return res.json();
  },

  getModelReport: async () => {
    const res = await fetch(`${API_BASE}/model/report`);
    return res.json();
  },

  // Timeline & Market Series
  getTimeline: async (from = '2020-01-01', to = '2025-12-31', family?: string, subtype?: string, direction?: string): Promise<TimelineResponse> => {
    const params = new URLSearchParams({ from, to });
    if (family) params.append('family', family);
    if (subtype) params.append('subtype', subtype);
    if (direction) params.append('impact_direction', direction);
    const res = await fetch(`${API_BASE}/timeline?${params.toString()}`);
    return res.json();
  },

  getMarketSeries: async (symbol = 'ASPI', from = '2020-01-01', to = '2025-12-31') => {
    const params = new URLSearchParams({ symbol, from, to });
    const res = await fetch(`${API_BASE}/market/series?${params.toString()}`);
    return res.json();
  },

  getMarketSymbols: async () => {
    const res = await fetch(`${API_BASE}/market/symbols`);
    return res.json();
  },

  // Events
  getEvents: async (params?: { family?: string; subtype?: string; date_from?: string; date_to?: string; keyword?: string; limit?: number }) => {
    const sp = new URLSearchParams();
    if (params?.family) sp.append('family', params.family);
    if (params?.subtype) sp.append('subtype', params.subtype);
    if (params?.date_from) sp.append('date_from', params.date_from);
    if (params?.date_to) sp.append('date_to', params.date_to);
    if (params?.keyword) sp.append('keyword', params.keyword);
    if (params?.limit) sp.append('limit', params.limit.toString());
    const res = await fetch(`${API_BASE}/events?${sp.toString()}`);
    return res.json();
  },

  getEventSummary: async () => {
    const res = await fetch(`${API_BASE}/events/summary`);
    return res.json();
  },

  getEventDetail: async (eventId: string): Promise<EventDetail> => {
    const res = await fetch(`${API_BASE}/events/${eventId}`);
    if (!res.ok) throw new Error('Event not found');
    return res.json();
  },

  // Prediction
  predictPolicy: async (payload: {
    policy_type: string;
    policy_headline: string;
    announcement_date: string;
    affected_sectors?: string[];
    target_symbol?: string;
    forecast_horizon?: number;
    historical_cutoff?: string;
  }): Promise<PredictionResult> => {
    const res = await fetch(`${API_BASE}/predict/policy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Policy prediction failed');
    return res.json();
  },

  predictArrest: async (payload: {
    person_name: string;
    event_description: string;
    event_subtype?: string;
    government_or_opposition?: string;
    announcement_date: string;
    crisis_or_protest?: string;
    forecast_horizon?: number;
    historical_cutoff?: string;
  }): Promise<PredictionResult> => {
    const res = await fetch(`${API_BASE}/predict/arrest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Political arrest prediction failed');
    return res.json();
  },

  predictScenarios: async (payload: {
    headline: string;
    event_family: string;
    event_subtype: string;
    event_date: string;
    forecast_horizon?: number;
  }) => {
    const res = await fetch(`${API_BASE}/predict/scenarios`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return res.json();
  },

  runBacktest: async (payload: {
    start_date?: string;
    end_date?: string;
    cutoff_date: string;
    event_family: string;
    target_symbol?: string;
    horizon_days?: number;
  }): Promise<BacktestResult> => {
    const res = await fetch(`${API_BASE}/backtest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Backtest execution failed');
    return res.json();
  },

  // News & Verification
  getLatestNews: async (limit = 30, family?: string): Promise<{ count: number; articles: NewsArticleItem[] }> => {
    const sp = new URLSearchParams({ limit: limit.toString() });
    if (family) sp.append('family', family);
    const res = await fetch(`${API_BASE}/news/latest?${sp.toString()}`);
    return res.json();
  },

  pollNews: async () => {
    const res = await fetch(`${API_BASE}/news/poll`, { method: 'POST' });
    return res.json();
  },

  getNewsSources: async () => {
    const res = await fetch(`${API_BASE}/news/sources`);
    return res.json();
  },

  verifyNews: async (payload: { headline_or_text?: string; article_url?: string }): Promise<VerificationResponse> => {
    const res = await fetch(`${API_BASE}/news/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Verification failed');
    return res.json();
  },

  // Live CSE Market
  getLiveStatus: async (): Promise<LiveMarketStatus> => {
    const res = await fetch(`${API_BASE}/live/status`);
    return res.json();
  },

  getLiveIndices: async (): Promise<LiveIndices> => {
    const res = await fetch(`${API_BASE}/live/indices`);
    return res.json();
  },

  getLiveOverview: async () => {
    const res = await fetch(`${API_BASE}/live/overview`);
    return res.json();
  },

  getLiveGainers: async () => {
    const res = await fetch(`${API_BASE}/live/gainers`);
    return res.json();
  },

  getLiveLosers: async () => {
    const res = await fetch(`${API_BASE}/live/losers`);
    return res.json();
  },

  getLiveSecurities: async (search?: string): Promise<ListedSecurity[]> => {
    const sp = new URLSearchParams();
    if (search) sp.append('search', search);
    const res = await fetch(`${API_BASE}/live/securities?${sp.toString()}`);
    return res.json();
  }
};
