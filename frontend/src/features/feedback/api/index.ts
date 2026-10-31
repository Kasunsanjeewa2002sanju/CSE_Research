import { z } from 'zod';
import { apiFetch } from '@/api/client';
import type { ReviewerFeedbackSubmission, FeedbackSubmissionResponse } from '../types';

export const feedbackSubmissionResponseSchema = z.object({
  status: z.string(),
  feedback_id: z.string(),
});

export async function submitReviewerFeedback(
  data: ReviewerFeedbackSubmission
): Promise<FeedbackSubmissionResponse> {
  return apiFetch('/user/feedback', feedbackSubmissionResponseSchema, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
