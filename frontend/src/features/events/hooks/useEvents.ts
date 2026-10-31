import { useEventsListQuery } from './useEventsData';

export function useEvents(category?: string) {
  return useEventsListQuery(category);
}
export { useEventsListQuery, useEventDetailQuery, useEventsCoverageQuery } from './useEventsData';
