import { useState } from 'react';
import { TrendingUp, ShieldCheck, FileSpreadsheet, Clock } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Badge } from '@/components/ui/Badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { PriceActivityTab } from '../components/PriceActivityTab';
import { DataQualityTab } from '../components/DataQualityTab';
import { TableExportTab } from '../components/TableExportTab';
import { useMeta } from '@/context/MetaContext';

export default function DataExplorerPage() {
  const [activeTab, setActiveTab] = useState<'price' | 'quality' | 'table'>('price');
  const { asOfDate } = useMeta();

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      {/* Top Header & Breadcrumbs */}
      <PageHeader
        title="CSE Market Data & Integrity Explorer"
        description="Longitudinal analysis of ASPI closing levels, S&P SL 20 comparative benchmarks, empirical stationarity tests, and full panel export (1994–2025)."
        breadcrumbs={[{ label: 'Home', to: '/' }, { label: 'Data Explorer' }]}
        badge={
          <Badge variant="navy" size="sm" className="hidden sm:inline-flex">
            30+ Year Panel
          </Badge>
        }
        actions={
          <div className="flex items-center gap-2 font-mono text-xs text-text-muted">
            <Clock className="h-3.5 w-3.5" />
            <span>Data As-Of: {asOfDate || '2025-12-31'}</span>
          </div>
        }
      />

      {/* Main Tabbed Content */}
      <main>
        <Tabs
          value={activeTab}
          onValueChange={(val) => setActiveTab(val as 'price' | 'quality' | 'table')}
        >
          {/* Tab Selection Navigation */}
          <div className="border-b border-border pb-px">
            <TabsList className="rounded-card border border-border bg-surface-subtle p-1">
              <TabsTrigger value="price" className="flex items-center gap-2 text-xs font-semibold">
                <TrendingUp className="h-4 w-4" />
                <span>Price & Market Activity</span>
              </TabsTrigger>
              <TabsTrigger
                value="quality"
                className="flex items-center gap-2 text-xs font-semibold"
              >
                <ShieldCheck className="h-4 w-4" />
                <span>Data Quality & Integrity Audit</span>
              </TabsTrigger>
              <TabsTrigger value="table" className="flex items-center gap-2 text-xs font-semibold">
                <FileSpreadsheet className="h-4 w-4" />
                <span>Tabular View & CSV Export</span>
              </TabsTrigger>
            </TabsList>
          </div>

          {/* Tab 1: Price and Activity */}
          <TabsContent value="price" className="mt-6">
            <PriceActivityTab />
          </TabsContent>

          {/* Tab 2: Data Quality & Audit */}
          <TabsContent value="quality" className="mt-6">
            <DataQualityTab />
          </TabsContent>

          {/* Tab 3: Table and Export */}
          <TabsContent value="table" className="mt-6">
            <TableExportTab />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
