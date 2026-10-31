import { useState, useCallback } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Skeleton } from '@/components/ui/Skeleton';
import { ContractError } from '@/components/ui/ContractError';
import { Button } from '@/components/ui/Button';
import { ChevronLeft, ChevronRight, Newspaper } from 'lucide-react';
import { NewsNav } from '../components/NewsNav';
import { NewsFilters, type NewsFiltersState } from '../components/NewsFilters';
import { NewsCard } from '../components/NewsCard';
import { NewsDetailDrawer } from '../components/NewsDetailDrawer';
import { useNewsItemsQuery, useNewsFeedsQuery } from '../hooks/useNewsData';
import type { NewsItem } from '../types';

const INITIAL_FILTERS: NewsFiltersState = {
  source: 'all',
  category: 'all',
  stage: 'all',
  relevance: 'all',
  language: 'all',
  evidenceStrength: 'all',
  search: '',
  fromDate: '',
  toDate: '',
};

export default function NewsPage() {
  const [filtersState, setFiltersState] = useState<NewsFiltersState>(INITIAL_FILTERS);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(24);
  const [selectedItem, setSelectedItem] = useState<NewsItem | null>(null);

  // Queries
  const {
    data: itemsData,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useNewsItemsQuery({
    page,
    pageSize,
    source: filtersState.source,
    category: filtersState.category,
    stage: filtersState.stage,
    relevance: filtersState.relevance,
    language: filtersState.language,
    evidenceStrength: filtersState.evidenceStrength,
    search: filtersState.search,
    fromDate: filtersState.fromDate,
    toDate: filtersState.toDate,
  });

  const { data: feedsData } = useNewsFeedsQuery();

  const handleFilterChange = useCallback((key: keyof NewsFiltersState, value: string) => {
    setFiltersState((prev) => ({ ...prev, [key]: value }));
    setPage(1);
  }, []);

  const handleResetFilters = useCallback(() => {
    setFiltersState(INITIAL_FILTERS);
    setPage(1);
  }, []);

  const totalItems = itemsData?.total ?? 0;
  const totalPages = itemsData?.total_pages ?? 1;
  const items = itemsData?.items ?? [];
  const activeFeedsCount = feedsData?.feeds.filter((f) => f.status === 'active').length ?? 8;
  const totalFeedsCount = feedsData?.feeds.length ?? 14;

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      {/* Page Header */}
      <PageHeader
        title="Live News Intelligence & Sentiment Stream"
        description="Continuous monitoring of verified Sri Lankan political, financial, and regulatory news feeds mapped to Colombo Stock Exchange trading days with FinBERT NLP attribution."
        breadcrumbs={[{ label: 'Home', to: '/' }, { label: 'News Intelligence' }]}
      />

      {/* Sub-Navigation */}
      <NewsNav
        totalArticles={totalItems}
        activeFeeds={activeFeedsCount}
        totalFeeds={totalFeedsCount}
        refreshIntervalSec={300}
        onRefresh={() => refetch()}
        isRefreshing={isFetching}
      />

      {/* Filters Bar */}
      <NewsFilters
        filtersState={filtersState}
        onChange={handleFilterChange}
        onReset={handleResetFilters}
        apiFilterOptions={itemsData?.filters}
        totalResults={totalItems}
      />

      {/* Contract Error Check */}
      {isError && error instanceof Error && 'isContractError' in error && (
        <ContractError
          endpoint="/api/v1/news/items"
          error={error}
          onRetry={() => refetch()}
        />
      )}

      {/* Network / Generic Error */}
      {isError && !(error instanceof Error && 'isContractError' in error) && (
        <ErrorState
          title="Unable to Load News Stream"
          message={error instanceof Error ? error.message : 'Failed to retrieve live news items.'}
          onRetry={() => refetch()}
        />
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-64 rounded-card border border-border bg-surface-white p-5">
              <div className="flex items-center justify-between">
                <Skeleton className="h-8 w-8 rounded-lg" />
                <Skeleton className="h-4 w-20" />
              </div>
              <Skeleton className="mt-4 h-4 w-1/3" />
              <Skeleton className="mt-2 h-6 w-full" />
              <Skeleton className="mt-2 h-4 w-4/5" />
              <div className="mt-6 flex gap-2">
                <Skeleton className="h-6 w-16 rounded-full" />
                <Skeleton className="h-6 w-16 rounded-full" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && items.length === 0 && (
        <EmptyState
          icon={Newspaper}
          title="No News Stories Found"
          description="Zero news stories match the active filter criteria. Try adjusting keywords, changing category, or clearing the date window."
          action={
            <Button variant="outline" size="sm" onClick={handleResetFilters}>
              Reset All Filters
            </Button>
          }
        />
      )}

      {/* News Card Grid */}
      {!isLoading && !isError && items.length > 0 && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((item) => (
              <NewsCard
                key={item.id}
                item={item}
                onSelect={(selected) => setSelectedItem(selected)}
              />
            ))}
          </div>

          {/* Pagination Controls */}
          <div className="flex flex-col items-center justify-between gap-4 border-t border-border pt-4 sm:flex-row">
            <div className="flex items-center gap-2 text-xs text-text-muted font-mono">
              <span>
                Showing <strong>{((page - 1) * pageSize) + 1}</strong> to{' '}
                <strong>{Math.min(page * pageSize, totalItems)}</strong> of{' '}
                <strong>{totalItems.toLocaleString()}</strong> articles
              </span>
              <span className="text-border">|</span>
              <label htmlFor="page-size-select" className="text-text-muted">Per page:</label>
              <select
                id="page-size-select"
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setPage(1);
                }}
                className="rounded border border-border bg-surface-white px-1.5 py-0.5 text-xs text-text-primary focus:border-accent"
              >
                <option value={12}>12</option>
                <option value={24}>24</option>
                <option value={48}>48</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="flex items-center gap-1 text-xs"
              >
                <ChevronLeft className="h-4 w-4" />
                <span>Previous</span>
              </Button>

              <span className="px-3 font-mono text-xs text-text-muted">
                Page <strong className="text-text-primary">{page}</strong> of{' '}
                <strong className="text-text-primary">{totalPages}</strong>
              </span>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="flex items-center gap-1 text-xs"
              >
                <span>Next</span>
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Article Detail Drawer */}
      <NewsDetailDrawer
        item={selectedItem}
        onClose={() => setSelectedItem(null)}
      />
    </div>
  );
}
