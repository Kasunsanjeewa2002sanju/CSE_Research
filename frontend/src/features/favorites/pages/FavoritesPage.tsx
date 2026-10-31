import { PageContainer } from '@/components/layout/PageContainer';
import { EmptyState } from '@/components/ui/EmptyState';
import { Bookmark, Search } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Link } from 'react-router-dom';

export default function FavoritesPage() {
  return (
    <PageContainer
      title="Saved Views & Bookmarked Events"
      description="Quickly access pinned models, event studies, and custom market queries."
      breadcrumbs={[{ label: 'Home', to: '/' }, { label: 'Favorites' }]}
    >
      <div className="mx-auto max-w-xl py-8">
        <EmptyState
          icon={Bookmark}
          title="No Bookmarked Views Yet"
          description="You can pin political event timelines, model diagnostic comparisons, and scenario projections to this board."
          action={
            <Button asChild variant="primary" icon={<Search className="h-4 w-4" />}>
              <Link to="/events">Explore Political Events</Link>
            </Button>
          }
        />
      </div>
    </PageContainer>
  );
}
