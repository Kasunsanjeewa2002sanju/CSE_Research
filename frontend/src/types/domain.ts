export type EventCategory = 'Presidential' | 'Parliamentary' | 'Provincial' | 'Crisis';

export type ModelFamily = 'tree' | 'linear' | 'deep_learning' | 'baseline';

export type FeatureSet = 'A' | 'B' | 'C';

export interface MarketRegime {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  description: string;
}
