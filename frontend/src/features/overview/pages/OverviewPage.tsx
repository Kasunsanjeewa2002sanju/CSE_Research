import { OverviewHero } from '../components/OverviewHero';
import { MarketOverviewStrip } from '../components/MarketOverviewStrip';
import { OverviewStatCards } from '../components/OverviewStatCards';
import { PredictionWorkflowSection } from '../components/PredictionWorkflowSection';
import { OverviewShortcuts } from '../components/OverviewShortcuts';
import { RecentNewsPreview } from '../components/RecentNewsPreview';
import { useMarketSummaryQuery } from '../hooks/useOverviewData';
import { useMeta } from '@/context/MetaContext';

export default function OverviewPage() {
  const { data: summary } = useMarketSummaryQuery();
  const { asOfDate } = useMeta();

  return (
    <div className="bg-surface-base min-h-screen pb-16">
      {/* 1. Light Hero with actions */}
      <OverviewHero />

      {/* 2. Market Overview Strip */}
      <MarketOverviewStrip summary={summary} asOfDate={asOfDate} />

      {/* Main Page Container */}
      <main className="mx-auto max-w-7xl space-y-10 px-4 pt-8 sm:px-6 lg:px-8">
        {/* 3. KPI StatCards with Sparklines */}
        <OverviewStatCards />

        {/* 4. Four-Step "How the Prediction Works" Section */}
        <PredictionWorkflowSection />

        {/* 5. Direct Module Shortcuts */}
        <OverviewShortcuts />

        {/* 6. Recent News & Semantic Sentiment Preview */}
        <RecentNewsPreview />
      </main>
    </div>
  );
}
