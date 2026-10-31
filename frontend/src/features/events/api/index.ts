import { apiFetch } from '@/api/client';
import {
  eventsListResponseSchema,
  eventDetailSchema,
  eventsCoverageSchema,
  politicalEventSchema,
} from '@/api/zod-schemas';
import type { EventsListResponse, EventDetail, EventsCoverage } from '@/api/types';

export { politicalEventSchema, eventsListResponseSchema, eventDetailSchema, eventsCoverageSchema };

export async function fetchEvents(category?: string): Promise<EventsListResponse> {
  return apiFetch('/events', eventsListResponseSchema, {
    searchParams: category && category !== 'All' ? { category } : undefined,
  });
}

export async function fetchEventDetail(eventId: string): Promise<EventDetail> {
  return apiFetch(`/events/${eventId}`, eventDetailSchema);
}

export async function fetchEventsCoverage(): Promise<EventsCoverage> {
  return apiFetch('/events/coverage', eventsCoverageSchema);
}
