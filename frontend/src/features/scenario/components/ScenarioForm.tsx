import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import type { ScenarioParams } from '../types';

export interface ScenarioFormProps {
  onSubmit: (params: ScenarioParams) => void;
  isLoading: boolean;
}

export function ScenarioForm({ onSubmit, isLoading }: ScenarioFormProps) {
  const [category, setCategory] = useState('Presidential');
  const [margin, setMargin] = useState(0.05);
  const [turnout, setTurnout] = useState(0.75);
  const [horizon, setHorizon] = useState(5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      event_category: category,
      margin,
      turnout,
      horizon_days: horizon,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Scenario Simulation Parameters</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4 font-mono text-xs">
          <div>
            <label className="text-muted-foreground mb-1 block">Event Category</label>
            <input
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="text-foreground w-full rounded border border-border bg-background px-3 py-2"
              required
            />
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div>
              <label className="text-muted-foreground mb-1 block">Victory Margin (e.g. 0.05)</label>
              <input
                type="number"
                step="0.01"
                value={margin}
                onChange={(e) => setMargin(parseFloat(e.target.value))}
                className="text-foreground w-full rounded border border-border bg-background px-3 py-2"
                required
              />
            </div>

            <div>
              <label className="text-muted-foreground mb-1 block">Turnout (e.g. 0.75)</label>
              <input
                type="number"
                step="0.01"
                value={turnout}
                onChange={(e) => setTurnout(parseFloat(e.target.value))}
                className="text-foreground w-full rounded border border-border bg-background px-3 py-2"
                required
              />
            </div>

            <div>
              <label className="text-muted-foreground mb-1 block">Forecast Horizon (Days)</label>
              <input
                type="number"
                value={horizon}
                onChange={(e) => setHorizon(parseInt(e.target.value, 10))}
                className="text-foreground w-full rounded border border-border bg-background px-3 py-2"
                required
              />
            </div>
          </div>

          <div className="pt-2">
            <Button type="submit" isLoading={isLoading} size="sm">
              Compute Conformal Return Forecast
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
