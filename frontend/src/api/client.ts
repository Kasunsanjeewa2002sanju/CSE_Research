import { z } from 'zod';
import { getApiBaseUrl } from '@/lib/env';

// ============================================================================
// Error Normalization
// ============================================================================

export interface NormalizedErrorDetails {
  status: number;
  code: string;
  message: string;
  requestId: string;
  endpoint: string;
  timestamp: string;
  rawPayload?: unknown;
  zodError?: z.ZodError;
}

export class ApiClientError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly requestId: string;
  public readonly endpoint: string;
  public readonly timestamp: string;
  public readonly rawPayload?: unknown;
  public readonly zodError?: z.ZodError;

  constructor(details: NormalizedErrorDetails) {
    super(details.message);
    this.name = 'ApiClientError';
    this.status = details.status;
    this.code = details.code;
    this.requestId = details.requestId;
    this.endpoint = details.endpoint;
    this.timestamp = details.timestamp;
    this.rawPayload = details.rawPayload;
    this.zodError = details.zodError;
  }
}

export class ContractValidationError extends ApiClientError {
  constructor(endpoint: string, zodError: z.ZodError, rawPayload: unknown, requestId: string) {
    super({
      status: 200,
      code: 'CONTRACT_MISMATCH',
      message: `Contract schema validation failed for ${endpoint}: ${zodError.issues.length} issue(s)`,
      requestId,
      endpoint,
      timestamp: new Date().toISOString(),
      rawPayload,
      zodError,
    });
    this.name = 'ContractValidationError';
  }
}

export class BackendOfflineError extends ApiClientError {
  constructor(endpoint: string, originalError: unknown, requestId: string) {
    super({
      status: 0,
      code: 'NETWORK_ERROR',
      message: `Backend service unavailable at ${endpoint}`,
      requestId,
      endpoint,
      timestamp: new Date().toISOString(),
      rawPayload: originalError instanceof Error ? originalError.message : String(originalError),
    });
    this.name = 'BackendOfflineError';
  }
}

export class RequestTimeoutError extends ApiClientError {
  constructor(endpoint: string, timeoutMs: number, requestId: string) {
    super({
      status: 408,
      code: 'TIMEOUT',
      message: `Request to ${endpoint} timed out after ${timeoutMs}ms`,
      requestId,
      endpoint,
      timestamp: new Date().toISOString(),
    });
    this.name = 'RequestTimeoutError';
  }
}

// ============================================================================
// Telemetry Registry for /_contract Dev Tool
// ============================================================================

export interface EndpointTelemetry {
  endpoint: string;
  method: string;
  lastStatus: number | 'OFFLINE' | 'TIMEOUT';
  lastLatencyMs: number;
  lastCalledAt: string;
  validationStatus: 'VALID' | 'SCHEMA_MISMATCH' | 'FAILED' | 'PENDING';
  errorDetails?: string;
  requestId: string;
}

const telemetryMap = new Map<string, EndpointTelemetry>();
const telemetryListeners = new Set<(telemetry: EndpointTelemetry[]) => void>();

export function getContractTelemetry(): EndpointTelemetry[] {
  return Array.from(telemetryMap.values());
}

export function subscribeContractTelemetry(
  listener: (telemetry: EndpointTelemetry[]) => void
): () => void {
  telemetryListeners.add(listener);
  listener(getContractTelemetry());
  return () => {
    telemetryListeners.delete(listener);
  };
}

function updateTelemetry(record: EndpointTelemetry) {
  telemetryMap.set(`${record.method}:${record.endpoint}`, record);
  const current = getContractTelemetry();
  telemetryListeners.forEach((l) => l(current));
}

// ============================================================================
// Fetch Client Options
// ============================================================================

export interface ApiFetchOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  timeoutMs?: number;
  maxRetries?: number;
  retryDelayMs?: number;
  searchParams?: Record<string, string | number | boolean | undefined>;
}

function generateRequestId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `req_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

// ============================================================================
// Core Fetch Wrapper
// ============================================================================

export async function apiFetch<T>(
  endpoint: string,
  schema: z.ZodType<T, z.ZodTypeDef, unknown>,
  options: ApiFetchOptions = {}
): Promise<T> {
  const method = (options.method || 'GET').toUpperCase();
  const isIdempotentGet = method === 'GET';
  const timeoutMs = options.timeoutMs ?? 8000;
  const maxRetries = isIdempotentGet ? (options.maxRetries ?? 2) : 0;
  const retryDelayMs = options.retryDelayMs ?? 400;

  const baseUrl = getApiBaseUrl().replace(/\/$/, '');
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

  // Build URL with search params
  const url = new URL(`${baseUrl}${cleanEndpoint}`);
  if (options.searchParams) {
    Object.entries(options.searchParams).forEach(([key, val]) => {
      if (val !== undefined && val !== null) {
        url.searchParams.append(key, String(val));
      }
    });
  }

  let attempt = 0;
  let lastError: ApiClientError | null = null;
  const startTime = Date.now();
  const requestId = generateRequestId();

  while (attempt <= maxRetries) {
    attempt++;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const headers: Record<string, string> = {
        Accept: 'application/json',
        'X-Request-Id': requestId,
        ...((options.headers as Record<string, string>) || {}),
      };

      let bodyPayload: BodyInit | undefined = undefined;
      if (options.body !== undefined) {
        headers['Content-Type'] = 'application/json';
        bodyPayload = JSON.stringify(options.body);
      }

      const res = await fetch(url.toString(), {
        ...options,
        method,
        headers,
        body: bodyPayload,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      const latencyMs = Date.now() - startTime;

      const serverRequestId = res.headers.get('x-request-id') || requestId;

      if (!res.ok) {
        let rawErrorBody: unknown = undefined;
        try {
          rawErrorBody = await res.json();
        } catch {
          rawErrorBody = await res.text();
        }

        const err = new ApiClientError({
          status: res.status,
          code: `HTTP_${res.status}`,
          message: `HTTP ${res.status} from ${cleanEndpoint}`,
          requestId: serverRequestId,
          endpoint: cleanEndpoint,
          timestamp: new Date().toISOString(),
          rawPayload: rawErrorBody,
        });

        // Retry on 5xx errors for idempotent GETs
        if (isIdempotentGet && res.status >= 500 && attempt <= maxRetries) {
          lastError = err;
          await new Promise((resolve) =>
            setTimeout(resolve, retryDelayMs * Math.pow(2, attempt - 1))
          );
          continue;
        }

        updateTelemetry({
          endpoint: cleanEndpoint,
          method,
          lastStatus: res.status,
          lastLatencyMs: latencyMs,
          lastCalledAt: new Date().toISOString(),
          validationStatus: 'FAILED',
          errorDetails: `HTTP ${res.status}`,
          requestId: serverRequestId,
        });

        throw err;
      }

      // Successful HTTP response -> validate contract
      const rawJson = await res.json();
      const parseResult = schema.safeParse(rawJson);

      if (!parseResult.success) {
        console.error(
          `[Rule FR4] Contract schema mismatch at ${cleanEndpoint}:`,
          parseResult.error
        );
        updateTelemetry({
          endpoint: cleanEndpoint,
          method,
          lastStatus: res.status,
          lastLatencyMs: latencyMs,
          lastCalledAt: new Date().toISOString(),
          validationStatus: 'SCHEMA_MISMATCH',
          errorDetails: `${parseResult.error.issues.length} Zod violation(s)`,
          requestId: serverRequestId,
        });

        throw new ContractValidationError(
          cleanEndpoint,
          parseResult.error,
          rawJson,
          serverRequestId
        );
      }

      updateTelemetry({
        endpoint: cleanEndpoint,
        method,
        lastStatus: res.status,
        lastLatencyMs: latencyMs,
        lastCalledAt: new Date().toISOString(),
        validationStatus: 'VALID',
        requestId: serverRequestId,
      });

      return parseResult.data;
    } catch (err: unknown) {
      clearTimeout(timeoutId);
      const latencyMs = Date.now() - startTime;

      if (err instanceof ApiClientError) {
        lastError = err;
        if (attempt > maxRetries) {
          throw err;
        }
      } else if (err instanceof DOMException && err.name === 'AbortError') {
        const timeoutErr = new RequestTimeoutError(cleanEndpoint, timeoutMs, requestId);
        lastError = timeoutErr;

        updateTelemetry({
          endpoint: cleanEndpoint,
          method,
          lastStatus: 'TIMEOUT',
          lastLatencyMs: latencyMs,
          lastCalledAt: new Date().toISOString(),
          validationStatus: 'FAILED',
          errorDetails: `Timed out after ${timeoutMs}ms`,
          requestId,
        });

        if (isIdempotentGet && attempt <= maxRetries) {
          await new Promise((resolve) =>
            setTimeout(resolve, retryDelayMs * Math.pow(2, attempt - 1))
          );
          continue;
        }
        throw timeoutErr;
      } else {
        const offlineErr = new BackendOfflineError(cleanEndpoint, err, requestId);
        lastError = offlineErr;

        updateTelemetry({
          endpoint: cleanEndpoint,
          method,
          lastStatus: 'OFFLINE',
          lastLatencyMs: latencyMs,
          lastCalledAt: new Date().toISOString(),
          validationStatus: 'FAILED',
          errorDetails: offlineErr.message,
          requestId,
        });

        if (isIdempotentGet && attempt <= maxRetries) {
          await new Promise((resolve) =>
            setTimeout(resolve, retryDelayMs * Math.pow(2, attempt - 1))
          );
          continue;
        }
        throw offlineErr;
      }
    }
  }

  throw lastError || new BackendOfflineError(cleanEndpoint, 'Max retries exhausted', requestId);
}

// ============================================================================
// Pagination Helper
// ============================================================================

export interface PaginatedParams {
  page?: number;
  pageSize?: number;
  [key: string]: string | number | boolean | undefined;
}

export async function fetchPaginated<T>(
  endpoint: string,
  itemSchema: z.ZodType<T, z.ZodTypeDef, unknown>,
  params: PaginatedParams = {}
) {
  const schema = z.object({
    items: z.array(itemSchema),
    total: z.number().int().nonnegative(),
    page: z.number().int().positive(),
    page_size: z.number().int().positive(),
    total_pages: z.number().int().nonnegative(),
    has_next: z.boolean(),
  });

  const searchParams: Record<string, string | number | boolean | undefined> = {
    page: params.page ?? 1,
    page_size: params.pageSize ?? 20,
    ...params,
  };

  return apiFetch(endpoint, schema, { searchParams });
}
