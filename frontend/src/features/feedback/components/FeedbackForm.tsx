import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import type { ReviewerFeedbackSubmission } from '../types';

export interface FeedbackFormProps {
  onSubmit: (data: ReviewerFeedbackSubmission) => void;
  isLoading: boolean;
}

export function FeedbackForm({ onSubmit, isLoading }: FeedbackFormProps) {
  const [role, setRole] = useState('Academic Reviewer');
  const [feature, setFeature] = useState('Event Study CAAR');
  const [clarity, setClarity] = useState(5);
  const [plausibility, setPlausibility] = useState(5);
  const [comments, setComments] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      user_role: role,
      feature_evaluated: feature,
      clarity_score: clarity,
      plausibility_score: plausibility,
      comments,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Peer Review & Study Evaluation Form</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4 font-mono text-xs">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="text-muted-foreground mb-1 block">Your Role / Affiliation</label>
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="text-foreground w-full rounded border border-border bg-background px-3 py-2 font-sans text-xs"
                required
              />
            </div>

            <div>
              <label className="text-muted-foreground mb-1 block">Feature Evaluated</label>
              <input
                type="text"
                value={feature}
                onChange={(e) => setFeature(e.target.value)}
                className="text-foreground w-full rounded border border-border bg-background px-3 py-2 font-sans text-xs"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="text-muted-foreground mb-1 block">
                Methodological Clarity (1 to 5)
              </label>
              <input
                type="number"
                min="1"
                max="5"
                value={clarity}
                onChange={(e) => setClarity(parseInt(e.target.value, 10))}
                className="text-foreground w-full rounded border border-border bg-background px-3 py-2"
                required
              />
            </div>

            <div>
              <label className="text-muted-foreground mb-1 block">
                Plausibility & Honesty (1 to 5)
              </label>
              <input
                type="number"
                min="1"
                max="5"
                value={plausibility}
                onChange={(e) => setPlausibility(parseInt(e.target.value, 10))}
                className="text-foreground w-full rounded border border-border bg-background px-3 py-2"
                required
              />
            </div>
          </div>

          <div>
            <label className="text-muted-foreground mb-1 block">
              Review Comments & Observations
            </label>
            <textarea
              rows={4}
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="Notes on statistical rigor, data presentation, or interface utility..."
              className="text-foreground w-full rounded border border-border bg-background p-3 font-sans text-xs"
              required
            />
          </div>

          <Button type="submit" isLoading={isLoading} size="sm">
            Submit Reviewer Feedback
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
