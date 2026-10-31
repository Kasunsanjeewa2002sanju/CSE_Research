/**
 * Unified TanStack Query Key Factory
 *
 * Provides strictly-typed query keys for all queries across the research platform.
 */

export const queryKeys = {
  meta: {
    all: ['meta'] as const,
    root: () => [...queryKeys.meta.all, 'root'] as const,
    glossary: () => [...queryKeys.meta.all, 'glossary'] as const,
    disclaimers: () => [...queryKeys.meta.all, 'disclaimers'] as const,
    stages: () => [...queryKeys.meta.all, 'stages'] as const,
    eventTypes: () => [...queryKeys.meta.all, 'eventTypes'] as const,
  },
  system: {
    all: ['system'] as const,
    health: () => [...queryKeys.system.all, 'health'] as const,
    status: () => [...queryKeys.system.all, 'status'] as const,
  },
  market: {
    all: ['market'] as const,
    summary: () => [...queryKeys.market.all, 'summary'] as const,
    series: (range?: string) => [...queryKeys.market.all, 'series', range ?? 'all'] as const,
    stats: () => [...queryKeys.market.all, 'stats'] as const,
    intraday: (metric?: string) => [...queryKeys.market.all, 'intraday', metric ?? 'all'] as const,
    latest: () => [...queryKeys.market.all, 'latest'] as const,
  },
  dataAudit: {
    all: ['dataAudit'] as const,
    summary: () => [...queryKeys.dataAudit.all, 'summary'] as const,
  },
  events: {
    all: ['events'] as const,
    list: (category?: string) => [...queryKeys.events.all, 'list', category ?? 'all'] as const,
    detail: (id: string) => [...queryKeys.events.all, 'detail', id] as const,
    coverage: () => [...queryKeys.events.all, 'coverage'] as const,
  },
  eventStudy: {
    all: ['eventStudy'] as const,
    caar: (params?: Record<string, unknown> | string) =>
      [...queryKeys.eventStudy.all, 'caar', params ?? {}] as const,
    heatmap: () => [...queryKeys.eventStudy.all, 'heatmap'] as const,
    perEvent: (params?: Record<string, unknown>) =>
      [...queryKeys.eventStudy.all, 'perEvent', params ?? {}] as const,
    summary: () => [...queryKeys.eventStudy.all, 'summary'] as const,
    subgroups: (window?: string) =>
      [...queryKeys.eventStudy.all, 'subgroups', window ?? '[-20, +20]'] as const,
    event: (id: string, window?: string) =>
      [...queryKeys.eventStudy.all, 'event', id, window ?? '[-20, +20]'] as const,
  },
  protocol: {
    all: ['protocol'] as const,
    phases: () => [...queryKeys.protocol.all, 'phases'] as const,
    dictionary: () => [...queryKeys.protocol.all, 'dictionary'] as const,
  },
  models: {
    all: ['models'] as const,
    leaderboard: () => [...queryKeys.models.all, 'leaderboard'] as const,
    predictions: (modelId?: string, horizon?: number) =>
      [...queryKeys.models.all, 'predictions', modelId ?? 'champion', horizon ?? 5] as const,
    dmTests: () => [...queryKeys.models.all, 'dmTests'] as const,
    ablation: () => [...queryKeys.models.all, 'ablation'] as const,
    artifacts: () => [...queryKeys.models.all, 'artifacts'] as const,
    detail: (modelId = 'catboost_reg_c_h5') => [...queryKeys.models.all, 'detail', modelId] as const,
    compare: (ids = '') => [...queryKeys.models.all, 'compare', ids] as const,
    statistics: () => [...queryKeys.models.all, 'statistics'] as const,
    final: () => [...queryKeys.models.all, 'final'] as const,
  },
  news: {
    all: ['news'] as const,
    items: (params?: Record<string, unknown>) =>
      [...queryKeys.news.all, 'items', params ?? {}] as const,
    itemDetail: (id: string) => [...queryKeys.news.all, 'item', id] as const,
    feeds: () => [...queryKeys.news.all, 'feeds'] as const,
    pipelineRuns: () => [...queryKeys.news.all, 'pipelineRuns'] as const,
    pipelineStats: () => [...queryKeys.news.all, 'pipelineStats'] as const,
  },
  scenarios: {
    all: ['scenarios'] as const,
    backtests: () => [...queryKeys.scenarios.all, 'backtests'] as const,
    evidence: (params?: Record<string, unknown>) =>
      [...queryKeys.scenarios.all, 'evidence', params ?? {}] as const,
    explanation: (id?: string) =>
      [...queryKeys.scenarios.all, 'explanation', id ?? 'default'] as const,
  },
  research: {
    all: ['research'] as const,
    index: () => [...queryKeys.research.all, 'index'] as const,
    auditReport: () => [...queryKeys.research.all, 'auditReport'] as const,
    exports: () => [...queryKeys.research.all, 'exports'] as const,
  },
  user: {
    all: ['user'] as const,
    favorites: () => [...queryKeys.user.all, 'favorites'] as const,
    sus: () => [...queryKeys.user.all, 'sus'] as const,
  },
};
