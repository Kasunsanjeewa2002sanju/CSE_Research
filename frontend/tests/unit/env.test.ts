import { describe, it, expect } from 'vitest';
import { getApiBaseUrl, getWsBaseUrl } from '@/lib/env';

describe('Environment Configuration (Rule FR2)', () => {
  it('reads validated API base URL', () => {
    const apiUrl = getApiBaseUrl();
    expect(apiUrl).toBeDefined();
    expect(apiUrl).toMatch(/^https?:\/\//);
  });

  it('reads validated WebSocket URL', () => {
    const wsUrl = getWsBaseUrl();
    expect(wsUrl).toBeDefined();
    expect(wsUrl).toMatch(/^wss?:\/\//);
  });
});
