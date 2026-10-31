import { Suspense, lazy } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Shell } from '@/components/layout/Shell';
import { ErrorPage } from '@/app/ErrorPage';
import NotFoundPage from '@/app/NotFoundPage';

// Route-level code splitting per Rule FR7
const OverviewPage = lazy(() => import('@/features/overview/pages/OverviewPage'));
const DataExplorerPage = lazy(() => import('@/features/data-explorer/pages/DataExplorerPage'));
const EventsPage = lazy(() => import('@/features/events/pages/EventsPage'));
const EventDetailPage = lazy(() => import('@/features/events/pages/EventDetailPage'));
const EventStudyPage = lazy(() => import('@/features/event-study/pages/EventStudyPage'));
const MethodologyPage = lazy(() => import('@/features/methodology/pages/MethodologyPage'));
const ModelLeaderboardPage = lazy(() => import('@/features/model-lab/pages/ModelLeaderboardPage'));
const ModelDetailPage = lazy(() => import('@/features/model-lab/pages/ModelDetailPage'));
const ModelComparePage = lazy(() => import('@/features/model-lab/pages/ModelComparePage'));
const ModelStatisticsPage = lazy(() => import('@/features/model-lab/pages/ModelStatisticsPage'));
const FinalModelPage = lazy(() => import('@/features/model-lab/pages/FinalModelPage'));
const NewsPage = lazy(() => import('@/features/news/pages/NewsPage'));
const NewsPipelinePage = lazy(() => import('@/features/news/pages/NewsPipelinePage'));
const ScenarioPage = lazy(() => import('@/features/scenario/pages/ScenarioPage'));
const ResearchPage = lazy(() => import('@/features/research/pages/ResearchPage'));
const FavoritesPage = lazy(() => import('@/features/favorites/pages/FavoritesPage'));
const FeedbackPage = lazy(() => import('@/features/feedback/pages/FeedbackPage'));

// Dev-only preview route: completely excluded in production builds
const DesignPreviewPage = import.meta.env.DEV
  ? lazy(() => import('../../dev/DesignPreviewPage'))
  : () => <Navigate to="/" replace />;

const ContractCatalogPage = import.meta.env.DEV
  ? lazy(() => import('../../dev/ContractCatalogPage'))
  : () => <Navigate to="/" replace />;

function PageFallback() {
  return (
    <div className="flex min-h-[400px] items-center justify-center p-8">
      <div className="space-y-2 text-center">
        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        <div className="text-muted-foreground font-mono text-xs">Loading module bundle...</div>
      </div>
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Shell />,
    errorElement: <ErrorPage />,
    children: [
      {
        index: true,
        element: (
          <Suspense fallback={<PageFallback />}>
            <OverviewPage />
          </Suspense>
        ),
      },
      {
        path: 'data',
        element: (
          <Suspense fallback={<PageFallback />}>
            <DataExplorerPage />
          </Suspense>
        ),
      },
      {
        path: 'data-explorer',
        element: <Navigate to="/data" replace />,
      },
      {
        path: 'events',
        element: (
          <Suspense fallback={<PageFallback />}>
            <EventsPage />
          </Suspense>
        ),
      },
      {
        path: 'events/:id',
        element: (
          <Suspense fallback={<PageFallback />}>
            <EventDetailPage />
          </Suspense>
        ),
      },
      {
        path: 'event-study',
        element: (
          <Suspense fallback={<PageFallback />}>
            <EventStudyPage />
          </Suspense>
        ),
      },
      {
        path: 'methodology',
        element: (
          <Suspense fallback={<PageFallback />}>
            <MethodologyPage />
          </Suspense>
        ),
      },
      {
        path: 'models',
        element: (
          <Suspense fallback={<PageFallback />}>
            <ModelLeaderboardPage />
          </Suspense>
        ),
      },
      {
        path: 'models/compare',
        element: (
          <Suspense fallback={<PageFallback />}>
            <ModelComparePage />
          </Suspense>
        ),
      },
      {
        path: 'models/statistics',
        element: (
          <Suspense fallback={<PageFallback />}>
            <ModelStatisticsPage />
          </Suspense>
        ),
      },
      {
        path: 'models/final',
        element: (
          <Suspense fallback={<PageFallback />}>
            <FinalModelPage />
          </Suspense>
        ),
      },
      {
        path: 'models/:id',
        element: (
          <Suspense fallback={<PageFallback />}>
            <ModelDetailPage />
          </Suspense>
        ),
      },
      {
        path: 'model-lab',
        element: <Navigate to="/models" replace />,
      },
      {
        path: 'news',
        element: (
          <Suspense fallback={<PageFallback />}>
            <NewsPage />
          </Suspense>
        ),
      },
      {
        path: 'news/pipeline',
        element: (
          <Suspense fallback={<PageFallback />}>
            <NewsPipelinePage />
          </Suspense>
        ),
      },
      {
        path: 'scenario',
        element: (
          <Suspense fallback={<PageFallback />}>
            <ScenarioPage />
          </Suspense>
        ),
      },
      {
        path: 'predictor',
        element: (
          <Suspense fallback={<PageFallback />}>
            <ScenarioPage />
          </Suspense>
        ),
      },
      {
        path: 'scenario-predictor',
        element: <Navigate to="/scenario" replace />,
      },
      {
        path: 'research',
        element: (
          <Suspense fallback={<PageFallback />}>
            <ResearchPage />
          </Suspense>
        ),
      },
      {
        path: 'favorites',
        element: (
          <Suspense fallback={<PageFallback />}>
            <FavoritesPage />
          </Suspense>
        ),
      },
      {
        path: 'feedback',
        element: (
          <Suspense fallback={<PageFallback />}>
            <FeedbackPage />
          </Suspense>
        ),
      },
      // Dev-only preview & contract catalog routes
      ...(import.meta.env.DEV
        ? [
            {
              path: '_design',
              element: (
                <Suspense fallback={<PageFallback />}>
                  <DesignPreviewPage />
                </Suspense>
              ),
            },
            {
              path: '_contract',
              element: (
                <Suspense fallback={<PageFallback />}>
                  <ContractCatalogPage />
                </Suspense>
              ),
            },
          ]
        : []),
      // 404 Route
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
]);
