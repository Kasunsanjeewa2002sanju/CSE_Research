import { apiFetch } from '@/api/client';
import { eventStudyCaarResponseSchema } from '@/api/zod-schemas';
import type { EventStudyCaarResponse } from '../types';

export async function fetchEventStudyCaar(): Promise<EventStudyCaarResponse> {
  return apiFetch('/event-study/caar', eventStudyCaarResponseSchema);
}
