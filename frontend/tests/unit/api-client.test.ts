import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { z } from 'zod';
import {
  apiFetch,
  fetchPaginated,
  ApiClientError,
  ContractValidationError,
  BackendOfflineError,
  RequestTimeoutError,
} from '@/api/client';

describe('API Client (Rule FR4: Contract First & Robust Client)', () => {
  const originalFetch = globalThis.fetch;
  const sampleSchema = z.object({
    id: z.string(),
    value: z.number(),
  });

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  describe('Successful Requests & Contract Validation', () => {
    it('returns typed data when response matches Zod schema', async () => {
      const mockResponse = { id: 'aspi_001', value: 12450.5 };
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'x-request-id': 'req_test_123' }),
        json: async () => mockResponse,
      });

      const result = await apiFetch('/test/endpoint', sampleSchema);
      expect(result).toEqual(mockResponse);
      expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    });

    it('throws ContractValidationError with Zod issues on schema violation', async () => {
      // Missing required field 'value' and 'id' is a number instead of string
      const invalidPayload = { id: 12345 };
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'x-request-id': 'req_mismatch_456' }),
        json: async () => invalidPayload,
      });

      await expect(apiFetch('/test/endpoint', sampleSchema)).rejects.toThrow(
        ContractValidationError
      );

      try {
        await apiFetch('/test/endpoint', sampleSchema);
      } catch (err: unknown) {
        expect(err).toBeInstanceOf(ContractValidationError);
        const contractErr = err as ContractValidationError;
        expect(contractErr.code).toBe('CONTRACT_MISMATCH');
        expect(contractErr.rawPayload).toEqual(invalidPayload);
        expect(contractErr.zodError).toBeDefined();
        expect(contractErr.zodError?.issues.length).toBeGreaterThan(0);
      }
    });
  });

  describe('Error Normalization', () => {
    it('normalizes HTTP 404 response with code, status, and requestId', async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        headers: new Headers({ 'x-request-id': 'req_404_id' }),
        json: async () => ({ detail: 'Resource not found' }),
      });

      try {
        await apiFetch('/unknown/resource', sampleSchema);
        expect.unreachable('Should have thrown ApiClientError');
      } catch (err: unknown) {
        expect(err).toBeInstanceOf(ApiClientError);
        const apiErr = err as ApiClientError;
        expect(apiErr.status).toBe(404);
        expect(apiErr.code).toBe('HTTP_404');
        expect(apiErr.requestId).toBe('req_404_id');
        expect(apiErr.endpoint).toBe('/unknown/resource');
      }
    });

    it('normalizes network errors into BackendOfflineError with status 0', async () => {
      globalThis.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));

      try {
        await apiFetch('/offline/service', sampleSchema, { maxRetries: 0 });
        expect.unreachable('Should have thrown BackendOfflineError');
      } catch (err: unknown) {
        expect(err).toBeInstanceOf(BackendOfflineError);
        const offlineErr = err as BackendOfflineError;
        expect(offlineErr.status).toBe(0);
        expect(offlineErr.code).toBe('NETWORK_ERROR');
      }
    });
  });

  describe('Retries with Backoff for Idempotent GET Requests', () => {
    it('retries idempotent GET requests on HTTP 500 and succeeds', async () => {
      let callCount = 0;
      globalThis.fetch = vi.fn().mockImplementation(async () => {
        callCount++;
        if (callCount === 1) {
          return {
            ok: false,
            status: 500,
            headers: new Headers(),
            json: async () => ({ error: 'Internal server error' }),
          };
        }
        return {
          ok: true,
          status: 200,
          headers: new Headers({ 'x-request-id': 'req_retry_ok' }),
          json: async () => ({ id: 'recovered', value: 99.9 }),
        };
      });

      const data = await apiFetch('/retry/endpoint', sampleSchema, {
        method: 'GET',
        maxRetries: 2,
        retryDelayMs: 10,
      });

      expect(data).toEqual({ id: 'recovered', value: 99.9 });
      expect(callCount).toBe(2);
    });

    it('does NOT retry non-idempotent POST requests on failure', async () => {
      let callCount = 0;
      globalThis.fetch = vi.fn().mockImplementation(async () => {
        callCount++;
        return {
          ok: false,
          status: 500,
          headers: new Headers(),
          json: async () => ({ error: 'Database conflict' }),
        };
      });

      await expect(
        apiFetch('/scenarios/predict', sampleSchema, {
          method: 'POST',
          body: { event: 'test' },
          maxRetries: 3, // Should be ignored because method is POST
        })
      ).rejects.toThrow(ApiClientError);

      expect(callCount).toBe(1);
    });
  });

  describe('Request Timeout & AbortController', () => {
    it('throws RequestTimeoutError when fetch exceeds timeoutMs', async () => {
      globalThis.fetch = vi.fn().mockImplementation((_, init) => {
        return new Promise((_, reject) => {
          if (init?.signal) {
            init.signal.addEventListener('abort', () => {
              const abortErr = new DOMException('The user aborted a request.', 'AbortError');
              reject(abortErr);
            });
          }
        });
      });

      await expect(
        apiFetch('/slow/endpoint', sampleSchema, {
          timeoutMs: 50,
          maxRetries: 0,
        })
      ).rejects.toThrow(RequestTimeoutError);
    });
  });

  describe('Pagination Helper', () => {
    it('appends page and page_size search params and validates paginated envelope', async () => {
      const itemSchema = z.object({
        id: z.string(),
        title: z.string(),
      });

      const paginatedData = {
        items: [{ id: 'news_1', title: 'CSE Market Index Rises' }],
        total: 100,
        page: 2,
        page_size: 10,
        total_pages: 10,
        has_next: true,
      };

      globalThis.fetch = vi.fn().mockImplementation(async (url: string) => {
        expect(url).toContain('page=2');
        expect(url).toContain('page_size=10');
        return {
          ok: true,
          status: 200,
          headers: new Headers(),
          json: async () => paginatedData,
        };
      });

      const result = await fetchPaginated('/news/items', itemSchema, {
        page: 2,
        pageSize: 10,
      });

      expect(result.items).toHaveLength(1);
      expect(result.page).toBe(2);
      expect(result.total).toBe(100);
      expect(result.has_next).toBe(true);
    });
  });
});
