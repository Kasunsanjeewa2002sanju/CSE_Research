import { useState } from 'react';
import {
  Button,
  IconButton,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  StatCard,
  Badge,
  Chip,
  Tabs,
  SegmentedControl,
  Select,
  Combobox,
  DateRangePicker,
  Tooltip,
  Dialog,
  Drawer,
  Table,
  Skeleton,
  EmptyState,
  ErrorState,
  ContractError,
  useToast,
  Stepper,
  PageHeader,
  Breadcrumbs,
  KeyValueList,
  CodeBlock,
  JsonViewer,
} from '@/components/ui';
import {
  ChartCard,
  EChart,
  createConfidenceBandSeries,
  createEventMarkLine,
  createEventWindowMarkArea,
  themeTokens,
} from '@/components/charts';
import {
  Sparkles,
  Download,
  AlertTriangle,
  Info,
  Layers,
  Search,
  Bell,
  BarChart2,
  LineChart as LineChartIcon,
} from 'lucide-react';
import type { EChartsOption } from 'echarts';

// Clearly marked constant banner
const DEV_WATERMARK = '[Design Preview Only — Not Production Data]';

export default function DesignPreviewPage() {
  const { toast } = useToast();

  // State controls for interactive preview components
  const [activeTab, setActiveTab] = useState('components');
  const [segmentedVal, setSegmentedVal] = useState('1M');
  const [selectVal, setSelectVal] = useState('aspi_close');
  const [comboboxVal, setComboboxVal] = useState('presidential');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [currentStage, setCurrentStage] = useState(3);
  const [dateRange, setDateRange] = useState({ start: '2024-01-01', end: '2024-09-30' });

  // Chart states
  const [chartState, setChartState] = useState<'normal' | 'loading' | 'empty' | 'error'>('normal');

  // Sample data for Table component (clearly marked design preview only)
  const sampleTableData = [
    {
      id: 'EVT-001',
      eventName: '[Design Preview Only] Presidential Election 2024',
      date: '2024-09-21',
      impact: 'High',
      aspiReaction: '+3.42%',
      pVal: '< 0.001',
    },
    {
      id: 'EVT-002',
      eventName: '[Design Preview Only] Central Bank Policy Rate Cut 250bps',
      date: '2024-03-26',
      impact: 'Critical',
      aspiReaction: '+1.88%',
      pVal: '0.012',
    },
    {
      id: 'EVT-003',
      eventName: '[Design Preview Only] Parliamentary Dissolution Proclamation',
      date: '2024-09-24',
      impact: 'Medium',
      aspiReaction: '-0.75%',
      pVal: '0.140',
    },
    {
      id: 'EVT-004',
      eventName: '[Design Preview Only] External Debt Restructuring Bilateral Accord',
      date: '2024-06-26',
      impact: 'High',
      aspiReaction: '+2.15%',
      pVal: '0.004',
    },
    {
      id: 'EVT-005',
      eventName: '[Design Preview Only] Provincial Council Delimitation Review',
      date: '2024-02-14',
      impact: 'Low',
      aspiReaction: '+0.12%',
      pVal: '0.620',
    },
  ];

  const tableColumns = [
    { key: 'id', header: 'Event ID', sortable: true, width: '110px' },
    { key: 'eventName', header: 'Event Title (Preview Only)', sortable: true },
    { key: 'date', header: 'Date', sortable: true, width: '120px' },
    {
      key: 'impact',
      header: 'Impact',
      sortable: true,
      width: '110px',
      render: (val: unknown) => {
        const str = String(val);
        const variant =
          str === 'Critical'
            ? 'danger'
            : str === 'High'
              ? 'warning'
              : str === 'Medium'
                ? 'primary'
                : 'neutral';
        return <Badge variant={variant as any}>{str}</Badge>;
      },
    },
    {
      key: 'aspiReaction',
      header: 'ASPI Δ (Preview)',
      sortable: true,
      width: '130px',
      render: (val: unknown) => {
        const str = String(val);
        const isPos = str.startsWith('+');
        return (
          <span className={`font-mono font-bold ${isPos ? 'text-data-up' : 'text-data-down'}`}>
            {str}
          </span>
        );
      },
    },
    { key: 'pVal', header: 'p-value', sortable: true, width: '90px' },
  ];

  // ECharts Time Series with Confidence Ribbons & Event MarkLines
  const dates = [
    '-20d',
    '-15d',
    '-10d',
    '-5d',
    '-3d',
    '-1d',
    'Event (t0)',
    '+1d',
    '+3d',
    '+5d',
    '+10d',
    '+15d',
    '+20d',
  ];
  const meanCaar = [
    0.0, -0.2, -0.4, -0.1, 0.3, 0.8, 1.9, 2.4, 2.8, 3.1, 2.9, 3.4, 3.8,
  ];
  const lowerBand = [
    -0.8, -1.1, -1.3, -1.0, -0.6, 0.0, 0.8, 1.2, 1.5, 1.7, 1.4, 1.8, 2.1,
  ];
  const upperBand = [
    0.8, 0.7, 0.6, 0.8, 1.2, 1.6, 2.9, 3.5, 4.0, 4.5, 4.3, 4.9, 5.5,
  ];

  const confidenceData = dates.map((d, i) => ({
    x: d,
    median: meanCaar[i],
    lower: lowerBand[i],
    upper: upperBand[i],
  }));

  const confidenceSeries = createConfidenceBandSeries(confidenceData, {
    bandName: '95% Placebo Bootstrap Band (Design Preview)',
    medianName: 'Mean CAAR (Design Preview)',
    bandColor: 'rgba(27, 92, 214, 0.16)',
    medianColor: themeTokens.accent,
  });

  if (confidenceSeries[2]) {
    confidenceSeries[2].markLine = createEventMarkLine('Event (t0)', 't0: Polling Day', themeTokens.dataDown) as any;
    confidenceSeries[2].markArea = createEventWindowMarkArea('-3d', '+3d', '[-3, +3] Event Window') as any;
  }

  const timeSeriesOption: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    legend: {
      data: [
        'Mean CAAR (Design Preview)',
        '95% Placebo Bootstrap Band (Design Preview)',
      ],
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '12%',
      top: '8%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%',
      },
    },
    series: confidenceSeries,
  };

  // Diverging Heatmap / Bar chart option
  const barChartOption: EChartsOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '8%', top: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ['Baseline AR', 'GARCH(1,1)', 'EGARCH', 'Ensemble A+B', 'Deep Sequence'],
    },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
    series: [
      {
        name: 'Directional Accuracy (Preview Only)',
        type: 'bar',
        data: [
          { value: 50.4, itemStyle: { color: themeTokens.muted } },
          { value: 54.2, itemStyle: { color: themeTokens.blueCobalt } },
          { value: 55.8, itemStyle: { color: themeTokens.blueVibrant } },
          { value: 58.6, itemStyle: { color: themeTokens.accent } },
          { value: 61.2, itemStyle: { color: themeTokens.dataUp } },
        ],
        barWidth: '40%',
        itemStyle: { borderRadius: [4, 4, 0, 0] },
      },
    ],
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Dev-only security header banner */}
      <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-center justify-between text-xs text-amber-900 dark:text-amber-200">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
          <span className="font-semibold">DEVELOPER DESIGN SYSTEM SHOWCASE (/_design)</span>
          <span className="hidden md:inline font-mono text-[11px] text-muted-foreground">
            {DEV_WATERMARK}
          </span>
        </div>
        <span className="px-2 py-0.5 rounded bg-amber-500/20 font-mono text-[10px] font-bold">
          DEV ONLY • TREE-SHAKEN IN PROD
        </span>
      </div>

      <PageHeader
        title="Design System & Component Showcase"
        description="Comprehensive verification sandbox showcasing all 24 atomic UI components, ECharts token themes, accessible fallbacks, and the 60/30/10 design tokens."
        breadcrumbs={[
          { label: 'Overview', to: '/' },
          { label: 'Design System Gallery (Dev)' },
        ]}
        badge={<Badge variant="accent">Stage F1 Verified</Badge>}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              icon={<Bell className="h-4 w-4" />}
              onClick={() => {
                toast({
                  title: 'Notification Triggered',
                  description: 'Toast component connected to global provider.',
                  variant: 'info',
                });
              }}
            >
              Test Toast
            </Button>
            <Button
              variant="primary"
              size="sm"
              icon={<Sparkles className="h-4 w-4" />}
              onClick={() => setDialogOpen(true)}
            >
              Open Dialog
            </Button>
          </div>
        }
      />

      {/* Tabs navigation across showcase sections */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'components', label: 'UI Components (24)', icon: Layers },
          { key: 'charts', label: 'ECharts Token Foundation', icon: LineChartIcon },
          { key: 'tables', label: 'Data Tables & Lists', icon: BarChart2 },
          { key: 'states', label: 'Feedback & Error States', icon: AlertTriangle },
        ]}
      />

      {/* SECTION 1: ATOMIC UI COMPONENTS */}
      {activeTab === 'components' && (
        <div className="space-y-8 animate-fadeIn">
          {/* Breadcrumbs Showcase Card */}
          <Card className="p-4 bg-surface-card border-border">
            <div className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wider">
              Breadcrumbs Component Pattern
            </div>
            <Breadcrumbs
              items={[
                { label: 'Overview', to: '/' },
                { label: 'Political Events', to: '/events' },
                { label: 'Presidential Election 2024' },
              ]}
            />
          </Card>

          {/* Palette Tokens Bar */}
          <Card className="p-6 space-y-4">
            <h3 className="font-heading font-bold text-lg text-foreground flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-accent" />
              60 / 30 / 10 Token Palette & Semantic Color Allocations
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs font-mono">
              <div className="p-3 rounded-lg border border-border bg-white dark:bg-card text-foreground">
                <div className="w-full h-8 rounded bg-background border border-border mb-2" />
                <div className="font-bold">60% Neutrals</div>
                <div className="text-[10px] text-muted-foreground">#FFFFFF / #F6F8FC</div>
              </div>
              <div className="p-3 rounded-lg border border-border bg-white dark:bg-card text-foreground">
                <div className="w-full h-8 rounded bg-blue-navy mb-2" />
                <div className="font-bold">30% Blue Navy</div>
                <div className="text-[10px] text-muted-foreground">#0A2A66 (Header/Type)</div>
              </div>
              <div className="p-3 rounded-lg border border-border bg-white dark:bg-card text-foreground">
                <div className="w-full h-8 rounded bg-blue-cobalt mb-2" />
                <div className="font-bold">30% Blue Cobalt</div>
                <div className="text-[10px] text-muted-foreground">#1246B3 (Active tabs)</div>
              </div>
              <div className="p-3 rounded-lg border border-border bg-white dark:bg-card text-foreground">
                <div className="w-full h-8 rounded bg-accent mb-2" />
                <div className="font-bold text-accent-hover">10% Cyan Accent</div>
                <div className="text-[10px] text-muted-foreground">#00B8D9 (CTA/Glow)</div>
              </div>
              <div className="p-3 rounded-lg border border-border bg-white dark:bg-card text-foreground">
                <div className="w-full h-8 rounded bg-data-up mb-2" />
                <div className="font-bold text-data-up">Semantic UP</div>
                <div className="text-[10px] text-muted-foreground">#0F9D6B (Data only)</div>
              </div>
              <div className="p-3 rounded-lg border border-border bg-white dark:bg-card text-foreground">
                <div className="w-full h-8 rounded bg-data-down mb-2" />
                <div className="font-bold text-data-down">Semantic DOWN</div>
                <div className="text-[10px] text-muted-foreground">#D93A3A (Data only)</div>
              </div>
            </div>
          </Card>

          {/* StatCards Row */}
          <div className="space-y-3">
            <h3 className="font-heading font-bold text-base text-foreground">
              StatCard Variants (Values, Deltas, Glossaries, Sparklines)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title="Current ASPI Index"
                value="11,842.50"
                delta={{ value: 142.3, percentage: 1.22, isPositive: true }}
                asOfLabel="Design Preview Only"
                glossaryTerm="ASPI (All Share Price Index)"
                glossaryDefinition="The principal benchmark stock index of the Colombo Stock Exchange covering all listed equity issues."
              />
              <StatCard
                title="Cumulative Abnormal Return"
                value="+3.85%"
                delta={{ value: -0.45, percentage: -0.45, isPositive: false }}
                asOfLabel="Design Preview Only"
                badgeText="[-3, +3] Window"
                glossaryTerm="CAAR"
                glossaryDefinition="Cumulative Average Abnormal Return calculated via Market Model residual aggregation across historical event windows."
              />
              <StatCard
                title="Active Tracked Events"
                value="48 Events"
                delta={{ value: 4, percentage: 9.1, isPositive: true }}
                asOfLabel="Design Preview Only"
              />
              <StatCard
                title="Walk-Forward Baseline Loss"
                value="0.042 RMSE"
                delta={{ value: -0.008, percentage: -16.0, isPositive: true }}
                asOfLabel="Design Preview Only"
                badgeText="P5 Test Split"
              />
            </div>
          </div>

          {/* Stepper (6 Election Stages) */}
          <Card className="p-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="space-y-1">
                <h3 className="font-heading font-bold text-base text-foreground">
                  Stepper (Six Constitutional Election Stages)
                </h3>
                <p className="text-xs text-muted-foreground">
                  Tracks chronological event progression through formal election phases.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setCurrentStage((s) => Math.max(1, s - 1))}
                  disabled={currentStage <= 1}
                >
                  Previous Stage
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setCurrentStage((s) => Math.min(6, s + 1))}
                  disabled={currentStage >= 6}
                >
                  Advance Stage
                </Button>
              </div>
            </div>
            <Stepper currentStage={currentStage} onStageClick={(s: number) => setCurrentStage(s)} />
          </Card>

          {/* Buttons & Action Controls */}
          <Card className="p-6 space-y-6">
            <CardHeader className="p-0 pb-3">
              <CardTitle className="text-base font-bold">Button Hierarchy & Interactive Elements</CardTitle>
              <CardDescription className="text-xs">
                Demonstrates primary accent (#00B8D9), secondary, outline, ghost, destructive, and icon buttons.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0 space-y-6">
              <div className="flex flex-wrap items-center gap-3">
                <Button variant="primary" icon={<Sparkles className="h-4 w-4" />}>
                  Primary Action (Accent #00B8D9)
                </Button>
                <Button variant="secondary">Secondary Button</Button>
                <Button variant="outline">Outline Button</Button>
                <Button variant="ghost">Ghost Button</Button>
                <Button variant="danger">Danger Action</Button>
                <Button isLoading variant="primary">
                  Loading State
                </Button>
                <IconButton
                  icon={<Bell className="h-4 w-4" />}
                  aria-label="Notification bell"
                  variant="outline"
                />
                <IconButton
                  icon={<Download className="h-4 w-4" />}
                  aria-label="Download export"
                  variant="secondary"
                />
              </div>

              {/* Badges & Chips */}
              <div className="space-y-3 pt-4 border-t border-border">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Badges & Categorical Chips
                </h4>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="accent">Accent Badge</Badge>
                  <Badge variant="primary">Primary Badge</Badge>
                  <Badge variant="success">Evidence: Robust</Badge>
                  <Badge variant="warning">Evidence: Emerging</Badge>
                  <Badge variant="danger">Evidence: Speculative</Badge>
                  <Badge variant="outline">Impact: Low</Badge>
                  <Badge variant="secondary">Impact: Medium</Badge>
                  <Badge variant="danger">Impact: Critical</Badge>
                  <Chip label="Presidential Election" active onRemove={() => {}} />
                  <Chip label="Monetary Policy Cut" active={false} onClick={() => {}} />
                  <Chip label="Cabinet Reshuffle" active onRemove={() => {}} />
                </div>
              </div>

              {/* Input & Form Controls */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-border">
                <div>
                  <label className="block text-xs font-medium text-foreground mb-1.5">
                    Segmented Horizon Control
                  </label>
                  <SegmentedControl
                    value={segmentedVal}
                    onChange={setSegmentedVal}
                    options={[
                      { value: '1W', label: '1W' },
                      { value: '1M', label: '1M' },
                      { value: '3M', label: '3M' },
                      { value: '1Y', label: '1Y' },
                      { value: 'ALL', label: 'ALL' },
                    ]}
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-foreground mb-1.5">
                    Select Metric Dropdown
                  </label>
                  <Select
                    value={selectVal}
                    onChange={(val: string) => setSelectVal(val)}
                    options={[
                      { value: 'aspi_close', label: 'ASPI Closing Index' },
                      { value: 'log_return', label: 'Daily Log Returns' },
                      { value: 'volatility', label: 'GARCH(1,1) Volatility' },
                    ]}
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-foreground mb-1.5">
                    Combobox Searchable Filter
                  </label>
                  <Combobox
                    value={comboboxVal}
                    onChange={setComboboxVal}
                    options={[
                      { value: 'presidential', label: 'Presidential Elections' },
                      { value: 'parliamentary', label: 'Parliamentary Elections' },
                      { value: 'provincial', label: 'Provincial Council' },
                      { value: 'crises', label: 'Constitutional Crises' },
                    ]}
                    placeholder="Filter category..."
                  />
                </div>
              </div>

              {/* Date Range Picker & Tooltip with Glossary */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-border items-center">
                <div>
                  <label className="block text-xs font-medium text-foreground mb-1.5">
                    Date Range Picker (Asia/Colombo UTC+5:30)
                  </label>
                  <DateRangePicker
                    startDate={dateRange.start}
                    endDate={dateRange.end}
                    onChange={(range: { startDate: string; endDate: string }) =>
                      setDateRange({ start: range.startDate, end: range.endDate })
                    }
                  />
                </div>

                <div className="flex items-center gap-4">
                  <Tooltip
                    content="Tooltips provide clear glossary definitions with zero jargon overload."
                    glossaryTerm="Conformal Prediction Band"
                    glossaryDefinition="Distribution-free non-parametric prediction intervals providing finite-sample valid coverage rates under weak exchangeability."
                  >
                    <Button variant="outline" size="sm" icon={<Info className="h-4 w-4" />}>
                      Hover For Glossary Tooltip
                    </Button>
                  </Tooltip>

                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setDrawerOpen(true)}
                    icon={<Layers className="h-4 w-4" />}
                  >
                    Open Side Drawer
                  </Button>
                </div>
              </div>
            </CardContent>
            <CardFooter className="p-0 pt-3 border-t border-border/40 text-[11px] text-muted-foreground font-mono">
              Interactive design tokens: 12px radius, 8pt spacing grid, soft shadows
            </CardFooter>
          </Card>
        </div>
      )}

      {/* SECTION 2: ECHARTS FOUNDATION */}
      {activeTab === 'charts' && (
        <div className="space-y-8 animate-fadeIn">
          {/* Controls for Chart Card States */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-lg bg-surface-muted border border-border">
            <div className="text-xs font-medium text-foreground">
              Test Chart State Handling (Loading, Error, Empty, Realtime):
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant={chartState === 'normal' ? 'primary' : 'outline'}
                onClick={() => setChartState('normal')}
              >
                Normal
              </Button>
              <Button
                size="sm"
                variant={chartState === 'loading' ? 'primary' : 'outline'}
                onClick={() => setChartState('loading')}
              >
                Loading
              </Button>
              <Button
                size="sm"
                variant={chartState === 'empty' ? 'primary' : 'outline'}
                onClick={() => setChartState('empty')}
              >
                Empty
              </Button>
              <Button
                size="sm"
                variant={chartState === 'error' ? 'danger' : 'outline'}
                onClick={() => setChartState('error')}
              >
                Error
              </Button>
            </div>
          </div>

          {/* Time Series CAAR with Confidence Ribbon Chart */}
          <ChartCard
            title="Cumulative Average Abnormal Returns (CAAR) Around Political Shocks"
            subtitle="Calculated over 41-day event windows [-20, +20] with 95% bootstrap confidence bands"
            infoTooltip="CAAR aggregates abnormal returns across all sampled Sri Lankan election events using the Market Model baseline."
            rangeSlot={
              <SegmentedControl
                value="41D"
                onChange={() => {}}
                options={[
                  { value: '21D', label: '[-10, +10]' },
                  { value: '41D', label: '[-20, +20]' },
                ]}
              />
            }
            dataTableData={dates.map((d, i) => ({
              Date: d,
              'Mean CAAR (%)': meanCaar[i],
              'Lower 95% Band (%)': lowerBand[i],
              'Upper 95% Band (%)': upperBand[i],
            }))}
            dataTableColumns={[
              { key: 'Date', header: 'Event Day', sortable: true },
              { key: 'Mean CAAR (%)', header: 'Mean CAAR', sortable: true },
              { key: 'Lower 95% Band (%)', header: 'Lower 95% CI', sortable: true },
              { key: 'Upper 95% Band (%)', header: 'Upper 95% CI', sortable: true },
            ]}
            isLoading={chartState === 'loading'}
            isEmpty={chartState === 'empty'}
            error={chartState === 'error' ? 'Econometric compute daemon timed out.' : null}
            onRetry={() => setChartState('normal')}
          >
            <EChart option={timeSeriesOption} height="360px" />
          </ChartCard>

          {/* Bar Chart with Token Palette */}
          <ChartCard
            title="Model Directional Accuracy Across Architectural Feature Sets"
            subtitle="Walk-forward out-of-sample directional prediction accuracy vs random walk baseline"
            dataTableData={[
              { Model: 'Baseline AR', Accuracy: '50.4%' },
              { Model: 'GARCH(1,1)', Accuracy: '54.2%' },
              { Model: 'EGARCH', Accuracy: '55.8%' },
              { Model: 'Ensemble A+B', Accuracy: '58.6%' },
              { Model: 'Deep Sequence', Accuracy: '61.2%' },
            ]}
            dataTableColumns={[
              { key: 'Model', header: 'Architecture', sortable: true },
              { key: 'Accuracy', header: 'Accuracy (OOS)', sortable: true },
            ]}
          >
            <EChart option={barChartOption} height="300px" />
          </ChartCard>
        </div>
      )}

      {/* SECTION 3: DATA TABLES & KEY VALUE LISTS */}
      {activeTab === 'tables' && (
        <div className="space-y-8 animate-fadeIn">
          {/* Interactive Sortable Data Table */}
          <Card className="p-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="space-y-1">
                <h3 className="font-heading font-bold text-base text-foreground">
                  Sortable Data Table with Sticky Header & CSV Export
                </h3>
                <p className="text-xs text-muted-foreground">
                  Includes column sorting, responsive layout, and data-driven badges.
                </p>
              </div>
            </div>

            <Table
              data={sampleTableData}
              columns={tableColumns}
              keyField="id"
              exportFileName="cse_political_events_preview.csv"
              emptyMessage="No events to preview."
            />
          </Card>

          {/* KeyValueList and CodeBlock/JsonViewer */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6 space-y-4">
              <h3 className="font-heading font-bold text-base text-foreground">
                KeyValueList Component
              </h3>
              <p className="text-xs text-muted-foreground">
                Standardized presentation for model hyperparameters and econometric statistics.
              </p>
              <KeyValueList
                items={[
                  { key: 'Estimation Window', value: '250 Trading Days [-280, -31]' },
                  { key: 'Event Window', value: '41 Trading Days [-20, +20]' },
                  { key: 'Benchmark Index', value: 'Colombo Stock Exchange ASPI' },
                  { key: 'Statistical Test', value: 'Patell Z & Generalized Sign Test' },
                  { key: 'Confidence Level', value: '95.0% Non-parametric Bootstrap' },
                  { key: 'Zero-Lookahead Mandate', value: 'Verified Walk-Forward Splits' },
                ]}
              />
            </Card>

            <Card className="p-6 space-y-4">
              <h3 className="font-heading font-bold text-base text-foreground">
                CodeBlock & JsonViewer Components
              </h3>
              <p className="text-xs text-muted-foreground">
                Syntax-highlighted display for API contract payloads and logs.
              </p>
              <CodeBlock
                title="Example Econometric Model Formula"
                language="python"
                code={`def calculate_abnormal_return(r_it, alpha_i, beta_i, r_mt):
    """
    Market Model Expected Return:
    E[R_it] = alpha_i + beta_i * R_mt
    AR_it = R_it - E[R_it]
    """
    expected_return = alpha_i + beta_i * r_mt
    return r_it - expected_return`}
              />
              <JsonViewer
                title="System Status Payload Sample"
                data={{
                  status: 'healthy',
                  as_of_date: '2024-09-30',
                  pipeline_version: '1.2.0',
                  rules_enforced: ['FR1', 'FR2', 'FR3', 'FR4', 'FR5'],
                  lookahead_leakage_detected: false,
                }}
              />
            </Card>
          </div>
        </div>
      )}

      {/* SECTION 4: FEEDBACK & ERROR STATES */}
      {activeTab === 'states' && (
        <div className="space-y-8 animate-fadeIn">
          {/* Empty States */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="p-6">
              <EmptyState
                icon={Search}
                title="No Political Events Found"
                description="Try broadening your date filter or selecting a different election classification."
                action={<Button size="sm">Reset Filter</Button>}
                gapMessage="Filter returned 0 records"
              />
            </Card>

            <Card className="p-6">
              <ErrorState
                title="Backend Market Feed Disconnected"
                message="Unable to reach the CSE quotation API. Retrying connection in background."
                onRetry={() => {
                  toast({
                    title: 'Retrying Connection',
                    description: 'Testing backend gateway health.',
                    variant: 'info',
                  });
                }}
              />
            </Card>
          </div>

          {/* Contract ValidationError Card */}
          <Card className="p-6 space-y-4">
            <h3 className="font-heading font-bold text-base text-foreground">
              Rule FR4 Contract Error Component
            </h3>
            <p className="text-xs text-muted-foreground">
              Fires automatically if backend response violates Zod schema contract boundaries.
            </p>
            <ContractError
              endpoint="/api/v1/event-study/caar"
              error={{
                name: 'ContractValidationError',
                message: 'Zod validation failed: missing required field "ci_lower_95"',
                zodError: {
                  issues: [
                    {
                      path: ['points', 0, 'ci_lower_95'],
                      message: 'Expected number, received undefined',
                    },
                  ],
                },
              }}
              onRetry={() => {
                toast({
                  title: 'Retried Contract Call',
                  description: 'Contract validation error acknowledged.',
                  variant: 'warning',
                });
              }}
            />
          </Card>

          {/* Skeleton Loaders */}
          <Card className="p-6 space-y-4">
            <h3 className="font-heading font-bold text-base text-foreground">
              Skeleton Loading Placeholders
            </h3>
            <div className="space-y-3">
              <Skeleton className="h-6 w-1/3" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-4/5" />
              <div className="grid grid-cols-3 gap-3 pt-2">
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-20 w-full" />
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Interactive Dialog Modal */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title="Interactive Dialog Modal"
        description="Accessible modal dialog conforming to WAI-ARIA with focus trapping and backdrop blur."
        footer={
          <div className="flex items-center justify-end gap-2">
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                setDialogOpen(false);
                toast({
                  title: 'Action Confirmed',
                  description: 'Dialog action handled gracefully.',
                  variant: 'success',
                });
              }}
            >
              Confirm Action
            </Button>
          </div>
        }
      >
        <div className="space-y-3 text-sm text-muted-foreground">
          <p>
            This dialog demonstrates responsive card styling, smooth 180ms modal transitions,
            accessible Esc key listener, and keyboard focus containment.
          </p>
          <div className="p-3 bg-surface-muted rounded-md text-xs font-mono text-foreground">
            Dialog ID: #dialog-sample-preview
          </div>
        </div>
      </Dialog>

      {/* Interactive Drawer */}
      <Drawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        title="Interactive Filter Drawer"
        position="right"
      >
        <div className="space-y-4 text-sm text-muted-foreground">
          <p>
            The Drawer component slides smoothly in from the edge of the viewport, supporting mobile
            navigation collapse and auxiliary filter panels.
          </p>
          <div className="space-y-2">
            <label className="text-xs font-semibold text-foreground">Select Horizon Filter</label>
            <Select
              value="1Y"
              onChange={() => {}}
              options={[
                { value: '6M', label: 'Last 6 Months' },
                { value: '1Y', label: 'Last 1 Year' },
                { value: '5Y', label: 'Last 5 Years' },
              ]}
            />
          </div>
          <Button variant="primary" className="w-full mt-4" onClick={() => setDrawerOpen(false)}>
            Apply & Close
          </Button>
        </div>
      </Drawer>
    </div>
  );
}
