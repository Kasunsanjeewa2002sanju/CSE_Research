export interface ReviewerFeedbackSubmission {
  user_role: string;
  feature_evaluated: string;
  clarity_score: number;
  plausibility_score: number;
  comments: string;
}

export interface FeedbackSubmissionResponse {
  status: string;
  feedback_id: string;
}
