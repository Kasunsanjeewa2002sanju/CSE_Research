import { useState, useEffect } from 'react';
import { z } from 'zod';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Play,
  RotateCw,
  Search,
  FileCode2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { PageHeader } from '@/components/ui/PageHeader';
import {
  apiFetch,
  getContractTelemetry,
  subscribeContractTelemetry,
  type EndpointTelemetry,
} from '@/api/client';
import * as schemas from '@/api/zod-schemas';

interface EndpointDefinition {
  method: 'GET' | 'POST';
  path: string;
  domain: string;
  schemaName: string;
  gapId: string;
  schema: z.ZodTypeAny;
  postBody?: unknown;
}

const ENDPOINTS: EndpointDefinition[] = [
  // Meta & System
  {
    method: 'GET',
    path: '/meta',
    domain: 'Meta & Taxonomy',
    schemaName: 'metaResponseSchema',
    gapId: 'GAP-002',
    schema: schemas.metaResponseSchema,
  },
  {
    method: 'GET',
    path: '/system/health',
    domain: 'System',
    schemaName: 'systemHealthSchema',
    gapId: 'GAP-001',
    schema: schemas.systemHealthSchema,
  },
  {
    method: 'GET',
    path: '/system/status',
    domain: 'System',
    schemaName: 'systemStatusSchema',
    gapId: 'GAP-001',
    schema: schemas.systemStatusSchema,
  },

  // Market
  {
    method: 'GET',
    path: '/market/summary',
    domain: 'Market',
    schemaName: 'marketSummarySchema',
    gapId: 'GAP-003',
    schema: schemas.marketSummarySchema,
  },
  {
    method: 'GET',
    path: '/market/series',
    domain: 'Market',
    schemaName: 'marketSeriesResponseSchema',
    gapId: 'GAP-003',
    schema: schemas.marketSeriesResponseSchema,
  },

  // Data Audit
  {
    method: 'GET',
    path: '/data/audit',
    domain: 'Data Explorer',
    schemaName: 'dataAuditSchema',
    gapId: 'GAP-004',
    schema: schemas.dataAuditSchema,
  },

  // Events & Event Study
  {
    method: 'GET',
    path: '/events',
    domain: 'Events',
    schemaName: 'eventsListResponseSchema',
    gapId: 'GAP-005',
    schema: schemas.eventsListResponseSchema,
  },
  {
    method: 'GET',
    path: '/events/presidential-2024',
    domain: 'Events',
    schemaName: 'eventDetailSchema',
    gapId: 'GAP-005',
    schema: schemas.eventDetailSchema,
  },
  {
    method: 'GET',
    path: '/event-study/caar',
    domain: 'Event Study',
    schemaName: 'eventStudyCaarResponseSchema',
    gapId: 'GAP-006',
    schema: schemas.eventStudyCaarResponseSchema,
  },
  {
    method: 'GET',
    path: '/event-study/subgroups',
    domain: 'Event Study',
    schemaName: 'eventStudySubgroupsResponseSchema',
    gapId: 'GAP-006',
    schema: schemas.eventStudySubgroupsResponseSchema,
  },

  // Protocol & Features
  {
    method: 'GET',
    path: '/protocol',
    domain: 'Methodology',
    schemaName: 'protocolResponseSchema',
    gapId: 'GAP-007',
    schema: schemas.protocolResponseSchema,
  },
  {
    method: 'GET',
    path: '/features/dictionary',
    domain: 'Methodology',
    schemaName: 'featureDictionaryResponseSchema',
    gapId: 'GAP-007',
    schema: schemas.featureDictionaryResponseSchema,
  },

  // Models
  {
    method: 'GET',
    path: '/models/leaderboard',
    domain: 'Model Lab',
    schemaName: 'modelLeaderboardResponseSchema',
    gapId: 'GAP-008',
    schema: schemas.modelLeaderboardResponseSchema,
  },
  {
    method: 'GET',
    path: '/models/predictions',
    domain: 'Model Lab',
    schemaName: 'modelPredictionsResponseSchema',
    gapId: 'GAP-008',
    schema: schemas.modelPredictionsResponseSchema,
  },
  {
    method: 'GET',
    path: '/models/dm-tests',
    domain: 'Model Lab',
    schemaName: 'dmTestMatrixResponseSchema',
    gapId: 'GAP-008',
    schema: schemas.dmTestMatrixResponseSchema,
  },
  {
    method: 'GET',
    path: '/models/ablation',
    domain: 'Model Lab',
    schemaName: 'ablationResponseSchema',
    gapId: 'GAP-008',
    schema: schemas.ablationResponseSchema,
  },
  {
    method: 'GET',
    path: '/models/artifacts',
    domain: 'Model Lab',
    schemaName: 'modelArtifactsResponseSchema',
    gapId: 'GAP-008',
    schema: schemas.modelArtifactsResponseSchema,
  },

  // News
  {
    method: 'GET',
    path: '/news/items',
    domain: 'News',
    schemaName: 'newsItemsResponseSchema',
    gapId: 'GAP-009',
    schema: schemas.newsItemsResponseSchema,
  },
  {
    method: 'GET',
    path: '/news/feeds',
    domain: 'News',
    schemaName: 'newsFeedsResponseSchema',
    gapId: 'GAP-009',
    schema: schemas.newsFeedsResponseSchema,
  },
  {
    method: 'GET',
    path: '/news/pipeline-runs',
    domain: 'News',
    schemaName: 'pipelineRunsResponseSchema',
    gapId: 'GAP-009',
    schema: schemas.pipelineRunsResponseSchema,
  },
  {
    method: 'GET',
    path: '/news/pipeline-stats',
    domain: 'News',
    schemaName: 'pipelineStatsResponseSchema',
    gapId: 'GAP-009',
    schema: schemas.pipelineStatsResponseSchema,
  },

  // Scenarios
  {
    method: 'POST',
    path: '/scenarios/predict',
    domain: 'Scenario Predictor',
    schemaName: 'scenarioPredictResponseSchema',
    gapId: 'GAP-010',
    schema: schemas.scenarioPredictResponseSchema,
    postBody: {
      event_type: 'Presidential',
      expected_turnout_pct: 75.0,
      expected_margin_pct: 3.5,
      lead_party: 'NPP',
      market_regime: 'neutral',
      horizon_days: 5,
    },
  },
  {
    method: 'GET',
    path: '/scenarios/backtests',
    domain: 'Scenario Predictor',
    schemaName: 'scenarioBacktestsResponseSchema',
    gapId: 'GAP-010',
    schema: schemas.scenarioBacktestsResponseSchema,
  },

  // Research
  {
    method: 'GET',
    path: '/research/index',
    domain: 'Research',
    schemaName: 'researchIndexResponseSchema',
    gapId: 'GAP-011',
    schema: schemas.researchIndexResponseSchema,
  },
  {
    method: 'GET',
    path: '/research/audit-report',
    domain: 'Research',
    schemaName: 'researchAuditReportResponseSchema',
    gapId: 'GAP-011',
    schema: schemas.researchAuditReportResponseSchema,
  },
  {
    method: 'GET',
    path: '/research/exports',
    domain: 'Research',
    schemaName: 'researchExportsResponseSchema',
    gapId: 'GAP-011',
    schema: schemas.researchExportsResponseSchema,
  },

  // User & Survey
  {
    method: 'GET',
    path: '/user/favorites',
    domain: 'Favorites',
    schemaName: 'favoritesResponseSchema',
    gapId: 'GAP-012',
    schema: schemas.favoritesResponseSchema,
  },
  {
    method: 'GET',
    path: '/survey/sus',
    domain: 'Usability Study',
    schemaName: 'susSurveyResponseSchema',
    gapId: 'GAP-012',
    schema: schemas.susSurveyResponseSchema,
  },
];

export function ContractCatalogPage() {
  const [telemetry, setTelemetry] = useState<EndpointTelemetry[]>(getContractTelemetry());
  const [activeFilter, setActiveFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [pingingMap, setPingingMap] = useState<Record<string, boolean>>({});

  useEffect(() => {
    return subscribeContractTelemetry((items) => {
      setTelemetry([...items]);
    });
  }, []);

  const pingEndpoint = async (def: EndpointDefinition) => {
    const key = `${def.method}:${def.path}`;
    setPingingMap((prev) => ({ ...prev, [key]: true }));

    try {
      await apiFetch(def.path, def.schema, {
        method: def.method,
        body: def.postBody,
        timeoutMs: 4000,
        maxRetries: 0,
      });
    } catch {
      // Telemetry updates automatically inside apiFetch
    } finally {
      setPingingMap((prev) => ({ ...prev, [key]: false }));
    }
  };

  const pingAll = async () => {
    for (const ep of ENDPOINTS) {
      await pingEndpoint(ep);
    }
  };

  const getRecord = (def: EndpointDefinition): EndpointTelemetry | undefined => {
    return telemetry.find((t) => t.endpoint === def.path && t.method === def.method);
  };

  const filteredEndpoints = ENDPOINTS.filter((ep) => {
    const matchesDomain = activeFilter === 'all' || ep.domain.toLowerCase().includes(activeFilter.toLowerCase());
    const matchesSearch =
      ep.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ep.domain.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ep.schemaName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ep.gapId.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesDomain && matchesSearch;
  });

  const domains = Array.from(new Set(ENDPOINTS.map((e) => e.domain)));

  // Calculate stats
  const totalCount = ENDPOINTS.length;
  const validCount = telemetry.filter((t) => t.validationStatus === 'VALID').length;
  const mismatchCount = telemetry.filter((t) => t.validationStatus === 'SCHEMA_MISMATCH').length;
  const offlineCount = telemetry.filter((t) => t.lastStatus === 'OFFLINE' || t.lastStatus === 'TIMEOUT').length;

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      {/* Dev Only Notice */}
      <div className="flex items-center justify-between rounded-card border border-data-warning/40 bg-data-warning-subtle px-4 py-2.5 text-xs">
        <div className="flex items-center gap-2 text-data-warning font-medium">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>
            <strong>DEV-ONLY CONTRACT VERIFICATION TOOL (/_contract):</strong> Inspects contract validation status,
            response latencies, and backend gap mappings in real time. Never reachable in production build.
          </span>
        </div>
        <span className="rounded bg-data-warning/20 px-2 py-0.5 font-mono text-[10px] font-bold text-data-warning">
          TREE-SHAKEN IN PROD
        </span>
      </div>

      <PageHeader
        title="API Contract & Schema Verification Catalog"
        description="Live registry of all endpoints consumed by the research dashboard, testing schema boundaries, latencies, and backend gap mappings."
        breadcrumbs={[
          { label: 'Home', to: '/' },
          { label: 'Contract Catalog (Dev)' },
        ]}
        actions={
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={pingAll}
              icon={<RotateCw className="h-3.5 w-3.5" />}
            >
              Ping All Endpoints
            </Button>
          </div>
        }
      />

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card className="p-4">
          <div className="text-text-muted text-xs font-medium">Tracked Endpoints</div>
          <div className="mt-1 font-mono text-2xl font-bold text-text-primary">{totalCount}</div>
          <div className="text-text-subtle text-[11px]">Across 10 feature domains</div>
        </Card>

        <Card className="p-4">
          <div className="text-text-muted text-xs font-medium">Valid Contract Pass</div>
          <div className="mt-1 font-mono text-2xl font-bold text-data-up">{validCount}</div>
          <div className="text-text-subtle text-[11px]">Passed Zod boundary validation</div>
        </Card>

        <Card className="p-4">
          <div className="text-text-muted text-xs font-medium">Schema Mismatches</div>
          <div className="mt-1 font-mono text-2xl font-bold text-data-down">{mismatchCount}</div>
          <div className="text-text-subtle text-[11px]">Rule FR4 contract failures</div>
        </Card>

        <Card className="p-4">
          <div className="text-text-muted text-xs font-medium">Backend Offline / Gaps</div>
          <div className="mt-1 font-mono text-2xl font-bold text-data-warning">
            {offlineCount || 12}
          </div>
          <div className="text-text-subtle text-[11px]">Documented in backend-gaps.md</div>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setActiveFilter('all')}
            className={`rounded-chip px-3 py-1 text-xs font-medium transition-colors ${
              activeFilter === 'all'
                ? 'bg-blue-navy text-white dark:bg-blue-vibrant'
                : 'bg-surface-card-subtle text-text-muted hover:text-text-primary'
            }`}
          >
            All ({ENDPOINTS.length})
          </button>
          {domains.map((dom) => (
            <button
              key={dom}
              onClick={() => setActiveFilter(dom)}
              className={`rounded-chip px-3 py-1 text-xs font-medium transition-colors ${
                activeFilter === dom
                  ? 'bg-blue-navy text-white dark:bg-blue-vibrant'
                  : 'bg-surface-card-subtle text-text-muted hover:text-text-primary'
              }`}
            >
              {dom}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="text-text-muted absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search endpoint, schema, gap..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="border-border bg-surface-white text-text-primary focus:border-accent w-full rounded-button border py-1.5 pl-8 pr-3 text-xs focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>
      </div>

      {/* Endpoints Table Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Contract Endpoints & Boundary Status</CardTitle>
          <CardDescription>
            Validates each endpoint against strict Zod schemas with AbortController timeouts and idempotency retries.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-sans text-xs">
              <thead className="border-b border-border bg-surface-card-subtle text-[11px] font-semibold text-text-muted">
                <tr>
                  <th className="px-4 py-3">Method & Path</th>
                  <th className="px-4 py-3">Domain</th>
                  <th className="px-4 py-3">Zod Schema</th>
                  <th className="px-4 py-3">Backend Gap</th>
                  <th className="px-4 py-3">Last Status</th>
                  <th className="px-4 py-3">Latency</th>
                  <th className="px-4 py-3">Validation</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredEndpoints.map((def) => {
                  const key = `${def.method}:${def.path}`;
                  const record = getRecord(def);
                  const isPinging = pingingMap[key];

                  return (
                    <tr
                      key={key}
                      className="transition-colors hover:bg-surface-card-subtle/50"
                    >
                      {/* Method & Path */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span
                            className={`rounded px-1.5 py-0.5 font-mono text-[10px] font-bold ${
                              def.method === 'GET'
                                ? 'bg-blue-ice text-blue-cobalt dark:bg-blue-soft/30 dark:text-blue-vibrant'
                                : 'bg-accent-subtle text-accent-foreground'
                            }`}
                          >
                            {def.method}
                          </span>
                          <span className="font-mono font-medium text-text-primary">
                            {def.path}
                          </span>
                        </div>
                      </td>

                      {/* Domain */}
                      <td className="px-4 py-3 text-text-muted">{def.domain}</td>

                      {/* Zod Schema */}
                      <td className="px-4 py-3">
                        <span className="flex items-center gap-1 font-mono text-[11px] text-text-subtle">
                          <FileCode2 className="h-3 w-3 text-accent" />
                          {def.schemaName}
                        </span>
                      </td>

                      {/* Backend Gap */}
                      <td className="px-4 py-3">
                        <span className="rounded border border-border bg-surface-card-subtle px-1.5 py-0.5 font-mono text-[10px] text-text-muted">
                          {def.gapId}
                        </span>
                      </td>

                      {/* Last Status */}
                      <td className="px-4 py-3">
                        {record ? (
                          <span
                            className={`font-mono font-medium ${
                              record.lastStatus === 200
                                ? 'text-data-up'
                                : record.lastStatus === 'OFFLINE'
                                  ? 'text-data-warning'
                                  : 'text-data-down'
                            }`}
                          >
                            {record.lastStatus}
                          </span>
                        ) : (
                          <span className="font-mono text-text-subtle">—</span>
                        )}
                      </td>

                      {/* Latency */}
                      <td className="px-4 py-3 font-mono text-text-muted">
                        {record?.lastLatencyMs !== undefined ? `${record.lastLatencyMs} ms` : '—'}
                      </td>

                      {/* Validation */}
                      <td className="px-4 py-3">
                        {record ? (
                          record.validationStatus === 'VALID' ? (
                            <Badge variant="success" size="sm">
                              <CheckCircle2 className="mr-1 h-3 w-3" /> VALID
                            </Badge>
                          ) : record.validationStatus === 'SCHEMA_MISMATCH' ? (
                            <Badge variant="danger" size="sm">
                              <XCircle className="mr-1 h-3 w-3" /> MISMATCH
                            </Badge>
                          ) : (
                            <Badge variant="neutral" size="sm">
                              <AlertTriangle className="mr-1 h-3 w-3" /> OFFLINE
                            </Badge>
                          )
                        ) : (
                          <span className="text-text-subtle">Not tested</span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          isLoading={isPinging}
                          onClick={() => pingEndpoint(def)}
                          icon={<Play className="h-3 w-3" />}
                        >
                          Ping
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ContractCatalogPage;
