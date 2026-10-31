import { z } from 'zod';
import * as schemas from './zod-schemas';

// Common
export type PaginatedQuery = z.infer<typeof schemas.paginatedQuerySchema>;

// Meta & System
export type MetricGlossaryItem = z.infer<typeof schemas.metricGlossaryItemSchema>;
export type ElectionStageItem = z.infer<typeof schemas.electionStageItemSchema>;
export type EventTypeItem = z.infer<typeof schemas.eventTypeItemSchema>;
export type NewsCategoryItem = z.infer<typeof schemas.newsCategoryItemSchema>;
export type SectorItem = z.infer<typeof schemas.sectorItemSchema>;
export type RefreshIntervals = z.infer<typeof schemas.refreshIntervalsSchema>;
export type ProjectInfo = z.infer<typeof schemas.projectInfoSchema>;
export type MetaResponse = z.infer<typeof schemas.metaResponseSchema>;
export type SystemHealth = z.infer<typeof schemas.systemHealthSchema>;
export type SystemStatus = z.infer<typeof schemas.systemStatusSchema>;

// Market
export type MarketSummary = z.infer<typeof schemas.marketSummarySchema>;
export type MarketSeriesPoint = z.infer<typeof schemas.marketSeriesPointSchema>;
export type MarketSeriesResponse = z.infer<typeof schemas.marketSeriesResponseSchema>;
export type MarketStats = z.infer<typeof schemas.marketStatsSchema>;
export type MarketIntradayPoint = z.infer<typeof schemas.marketIntradayPointSchema>;
export type MarketIntradayResponse = z.infer<typeof schemas.marketIntradayResponseSchema>;
export type { LiveMarketSnapshot } from '@/stores/market-store';

// Data Audit
export type TradingDaysYear = z.infer<typeof schemas.tradingDaysYearSchema>;
export type DictionaryColumn = z.infer<typeof schemas.dictionaryColumnSchema>;
export type StationarityTest = z.infer<typeof schemas.stationarityTestSchema>;
export type DataAudit = z.infer<typeof schemas.dataAuditSchema>;

// Events
export type PoliticalEvent = z.infer<typeof schemas.politicalEventSchema>;
export type EventsListResponse = z.infer<typeof schemas.eventsListResponseSchema>;
export type EventDetailStage = z.infer<typeof schemas.eventDetailStageSchema>;
export type EventDetail = z.infer<typeof schemas.eventDetailSchema>;
export type UncoveredType = z.infer<typeof schemas.uncoveredTypeSchema>;
export type EventsCoverage = z.infer<typeof schemas.eventsCoverageSchema>;

// Event Study
export type CaarDataPoint = z.infer<typeof schemas.caarDataPointSchema>;
export type IndividualEventCarPoint = z.infer<typeof schemas.individualEventCarPointSchema>;
export type IndividualEventStudyPath = z.infer<typeof schemas.individualEventStudyPathSchema>;
export type PermutationBin = z.infer<typeof schemas.permutationBinSchema>;
export type PermutationDistribution = z.infer<typeof schemas.permutationDistributionSchema>;
export type CaarStats = z.infer<typeof schemas.caarStatsSchema>;
export type EventStudyCaarResponse = z.infer<typeof schemas.eventStudyCaarResponseSchema>;
export type EventStudySubgroup = z.infer<typeof schemas.eventStudySubgroupSchema>;
export type EventStudySubgroupsResponse = z.infer<typeof schemas.eventStudySubgroupsResponseSchema>;
export type HeatmapCell = z.infer<typeof schemas.heatmapCellSchema>;
export type EventStudyHeatmapResponse = z.infer<typeof schemas.eventStudyHeatmapResponseSchema>;
export type EventStudyPerEventItem = z.infer<typeof schemas.eventStudyPerEventItemSchema>;
export type EventStudyPerEventResponse = z.infer<typeof schemas.eventStudyPerEventResponseSchema>;
export type EventStudySummaryResponse = z.infer<typeof schemas.eventStudySummaryResponseSchema>;

// Protocol & Features
export type ProtocolPhase = z.infer<typeof schemas.protocolPhaseSchema>;
export type LeakageTestStatus = z.infer<typeof schemas.leakageTestStatusSchema>;
export type TargetDefinition = z.infer<typeof schemas.targetDefinitionSchema>;
export type LeakageTestItem = z.infer<typeof schemas.leakageTestItemSchema>;
export type PipelineStage = z.infer<typeof schemas.pipelineStageSchema>;
export type BaselineDefinition = z.infer<typeof schemas.baselineDefinitionSchema>;
export type ProtocolResponse = z.infer<typeof schemas.protocolResponseSchema>;
export type PhaseEventCoverageItem = z.infer<typeof schemas.phaseEventCoverageItemSchema>;
export type FeatureDictionaryItem = z.infer<typeof schemas.featureDictionaryItemSchema>;
export type FeatureDictionaryResponse = z.infer<typeof schemas.featureDictionaryResponseSchema>;

// Models
export type LeaderboardResponse = z.infer<typeof schemas.modelLeaderboardResponseSchema>;
export type PredictionItem = z.infer<typeof schemas.predictionItemSchema>;
export type ModelPredictionsResponse = z.infer<typeof schemas.modelPredictionsResponseSchema>;
export type DmTestPair = z.infer<typeof schemas.dmTestPairSchema>;
export type DmTestMatrixResponse = z.infer<typeof schemas.dmTestMatrixResponseSchema>;
export type AblationResponse = z.infer<typeof schemas.ablationResponseSchema>;
export type ModelArtifactItem = z.infer<typeof schemas.modelArtifactItemSchema>;
export type ModelArtifactsResponse = z.infer<typeof schemas.modelArtifactsResponseSchema>;

// News & Pipeline Monitor
export type DuplicateClusterItem = z.infer<typeof schemas.duplicateClusterItemSchema>;
export type NewsFilters = z.infer<typeof schemas.newsFiltersSchema>;
export type NewsItem = z.infer<typeof schemas.newsItemSchema>;
export type NewsItemsResponse = z.infer<typeof schemas.newsItemsResponseSchema>;
export type NewsItemDetailResponse = z.infer<typeof schemas.newsItemDetailResponseSchema>;
export type NewsFeedItem = z.infer<typeof schemas.newsFeedItemSchema>;
export type NewsFeedsResponse = z.infer<typeof schemas.newsFeedsResponseSchema>;
export type PipelineRunItem = z.infer<typeof schemas.pipelineRunItemSchema>;
export type PipelineRunsResponse = z.infer<typeof schemas.pipelineRunsResponseSchema>;
export type FailureLogItem = z.infer<typeof schemas.failureLogItemSchema>;
export type ItemsPerHourItem = z.infer<typeof schemas.itemsPerHourItemSchema>;
export type ClassificationDistributionItem = z.infer<typeof schemas.classificationDistributionItemSchema>;
export type LanguageSplitItem = z.infer<typeof schemas.languageSplitItemSchema>;
export type RelevanceFunnelStage = z.infer<typeof schemas.relevanceFunnelStageSchema>;
export type RelevanceFunnel = z.infer<typeof schemas.relevanceFunnelSchema>;
export type PipelineStatsSummary = z.infer<typeof schemas.pipelineStatsSummarySchema>;
export type PipelineStatsResponse = z.infer<typeof schemas.pipelineStatsResponseSchema>;

// Scenarios (Stage F9)
export type ScenarioSubmitRequest = z.infer<typeof schemas.scenarioSubmitRequestSchema>;
export type ScenarioPredictRequest = z.infer<typeof schemas.scenarioPredictRequestSchema>;
export type ScenarioPredictResponse = z.infer<typeof schemas.scenarioPredictResponseSchema>;
export type ScenarioHorizon = z.infer<typeof schemas.scenarioHorizonSchema>;
export type ScenarioPanel = z.infer<typeof schemas.scenarioPanelSchema>;
export type ScenarioEvidence = z.infer<typeof schemas.scenarioEvidenceSchema>;
export type ScenarioComparisonRow = z.infer<typeof schemas.scenarioComparisonRowSchema>;
export type ScenarioComparisonMatrix = z.infer<typeof schemas.scenarioComparisonMatrixSchema>;
export type ScenarioSubmitResponse = z.infer<typeof schemas.scenarioSubmitResponseSchema>;
export type ScenarioBacktestItem = z.infer<typeof schemas.scenarioBacktestItemSchema>;
export type ScenarioBacktestsSummary = z.infer<typeof schemas.scenarioBacktestsSummarySchema>;
export type ScenarioBacktestsResponse = z.infer<typeof schemas.scenarioBacktestsResponseSchema>;

// Research
export type ResearchDocument = z.infer<typeof schemas.researchDocumentSchema>;
export type ResearchIndexResponse = z.infer<typeof schemas.researchIndexResponseSchema>;
export type AuditDimension = z.infer<typeof schemas.auditDimensionSchema>;
export type ResearchAuditReportResponse = z.infer<typeof schemas.researchAuditReportResponseSchema>;
export type ResearchExportItem = z.infer<typeof schemas.researchExportItemSchema>;
export type ResearchExportsResponse = z.infer<typeof schemas.researchExportsResponseSchema>;

// User
export const susQuestionSchema = schemas.susQuestionSchema;
export type FavoriteItem = z.infer<typeof schemas.favoriteItemSchema>;
export type FavoritesResponse = z.infer<typeof schemas.favoritesResponseSchema>;
export type SusQuestion = z.infer<typeof schemas.susQuestionSchema>;
export type SusSurveyResponse = z.infer<typeof schemas.susSurveyResponseSchema>;

// Models (Stage F7)
export type ModelLeaderboardItem = z.infer<typeof schemas.modelLeaderboardItemSchema>;
export type ModelLeaderboardResponse = z.infer<typeof schemas.modelLeaderboardResponseSchema>;
export type ModelPredictionPoint = z.infer<typeof schemas.modelPredictionPointSchema>;
export type ModelCumulativeErrorPoint = z.infer<typeof schemas.modelCumulativeErrorPointSchema>;
export type ModelResidualHistogramBin = z.infer<typeof schemas.modelResidualHistogramBinSchema>;
export type ModelQQPoint = z.infer<typeof schemas.modelQQPointSchema>;
export type ModelResidualDiagnostics = z.infer<typeof schemas.modelResidualDiagnosticsSchema>;
export type ModelFeatureImportance = z.infer<typeof schemas.modelFeatureImportanceSchema>;
export type ModelTrainingCurvePoint = z.infer<typeof schemas.modelTrainingCurvePointSchema>;
export type ModelConfusionMatrix = z.infer<typeof schemas.modelConfusionMatrixSchema>;
export type ModelArtifact = z.infer<typeof schemas.modelArtifactSchema>;
export type ModelDetailResponse = z.infer<typeof schemas.modelDetailResponseSchema>;
export type ModelCompareResponse = z.infer<typeof schemas.modelCompareResponseSchema>;
export type DieboldMarianoTestItem = z.infer<typeof schemas.dieboldMarianoTestItemSchema>;
export type ModelConfidenceSet = z.infer<typeof schemas.modelConfidenceSetSchema>;
export type FeatureSetAblationItem = z.infer<typeof schemas.featureSetAblationItemSchema>;
export type EventWindowAblationItem = z.infer<typeof schemas.eventWindowAblationItemSchema>;
export type ModelStatisticsResponse = z.infer<typeof schemas.modelStatisticsResponseSchema>;
export type FinalModelResponse = z.infer<typeof schemas.finalModelResponseSchema>;
