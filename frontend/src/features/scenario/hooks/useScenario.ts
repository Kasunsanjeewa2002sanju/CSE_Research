import { useMutation } from '@tanstack/react-query';
import { evaluateScenario } from '../api';
import type { ScenarioParams, ScenarioResult } from '../types';

export function useScenarioEvaluation() {
  return useMutation<ScenarioResult, Error, ScenarioParams>({
    mutationFn: evaluateScenario,
  });
}
