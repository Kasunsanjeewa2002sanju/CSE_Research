import { PageContainer } from '@/components/layout/PageContainer';
import { FeedbackForm } from '../components/FeedbackForm';
import { useFeedbackSubmission } from '../hooks/useFeedback';
import { EmptyState } from '@/components/feedback/EmptyState';
import { Alert } from '@/components/ui/Alert';

export default function FeedbackPage() {
  const mutation = useFeedbackSubmission();

  return (
    <PageContainer
      title="Peer Reviewer & Student Study Feedback"
      description="Collect structured evaluations on interface usability, methodological honesty, and econometric interpretability."
    >
      <div className="space-y-6">
        {mutation.isSuccess && (
          <Alert variant="success" title="Feedback Recorded">
            Thank you! Your reviewer assessment was logged with ID:{' '}
            <span className="font-mono">{mutation.data.feedback_id}</span>.
          </Alert>
        )}

        <FeedbackForm onSubmit={(data) => mutation.mutate(data)} isLoading={mutation.isPending} />

        {mutation.isError && (
          <EmptyState
            title="Feedback Submission Service Pending"
            message="User feedback ingestion endpoint is pending backend gateway exposure."
            gapId="GAP-005"
          />
        )}
      </div>
    </PageContainer>
  );
}
