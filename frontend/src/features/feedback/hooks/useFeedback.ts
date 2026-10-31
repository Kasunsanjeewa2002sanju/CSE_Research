import { useMutation } from '@tanstack/react-query';
import { submitReviewerFeedback } from '../api';
import type { ReviewerFeedbackSubmission, FeedbackSubmissionResponse } from '../types';

export function useFeedbackSubmission() {
  return useMutation<FeedbackSubmissionResponse, Error, ReviewerFeedbackSubmission>({
    mutationFn: submitReviewerFeedback,
  });
}
