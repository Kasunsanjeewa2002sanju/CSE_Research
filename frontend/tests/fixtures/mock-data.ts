/**
 * Test Fixtures (Strictly for tests/ only, never imported in src/ per Rule FR3)
 */

export const testOverviewPayload = {
  aspi_current: 11450.25,
  daily_return: 0.0124,
  sample_size_events: 24,
  champion_model_name: 'CatBoostRegressor',
  champion_oos_r2: 0.0548,
  champion_directional_accuracy: 0.6117,
  data_as_of: '2026-10-13',
  is_stale: false,
  disclaimer: 'Historical association, not causation.',
};

export const testInvalidPayload = {
  aspi_current: 'NOT_A_NUMBER', // Violation
  daily_return: 0.0124,
};
