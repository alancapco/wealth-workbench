/**
 * Canonical API layer for the WM Workbench.
 *
 * Every screen calls these helpers. No screen embeds fixture objects or
 * invented numbers. Responses are unwrapped from the canonical
 * `{ data, meta }` envelope when present, and mutations carry the CSRF header
 * required by the backend's mutation guard.
 */
import axios, { AxiosError } from 'axios';

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const API_PREFIX = '/api/v1';
export const CSRF_TOKEN = 'workbench-ui';

export type Method = 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';

const http = axios.create({
  baseURL: `${API_BASE}${API_PREFIX}`,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
  timeout: 20000,
});

export class ApiError extends Error {
  status: number;
  code?: string;
  detail?: unknown;
  constructor(message: string, status: number, code?: string, detail?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.detail = detail;
  }
}

export interface CallOptions {
  query?: Record<string, string | number | boolean | null | undefined>;
  body?: unknown;
  headers?: Record<string, string>;
  /** LLM-backed projections can exceed the default 20s client timeout. */
  timeout?: number;
}

export interface ApiResult<T> {
  data: T;
  raw: unknown;
  status: number;
  meta?: Record<string, unknown>;
}

/** Unwrap `{ data, meta }` envelopes; leave bare payloads untouched. */
export function unwrap<T = any>(payload: any): T {
  if (
    payload &&
    typeof payload === 'object' &&
    !Array.isArray(payload) &&
    'data' in payload &&
    'meta' in payload
  ) {
    return payload.data as T;
  }
  return payload as T;
}

function errorMessage(err: AxiosError<any>): string {
  const d = err.response?.data;
  if (!d) return err.message || 'Network error';
  if (typeof d === 'string') return d;
  if (d.error?.message) return d.error.message;
  if (d.detail?.error?.message) return d.detail.error.message;
  if (d.detail?.message) return d.detail.message;
  if (typeof d.detail === 'string') return d.detail;
  if (Array.isArray(d.detail)) {
    return d.detail
      .map((x: any) => `${(x.loc || []).join('.')}: ${x.msg || x.message || ''}`)
      .join(' · ');
  }
  return err.message || 'Request failed';
}

/** Execute any API call. Path is relative to /api/v1 (or a full URL). */
export async function call<T = any>(
  method: Method,
  path: string,
  opts: CallOptions = {},
): Promise<ApiResult<T>> {
  const isMutation = method !== 'GET';
  const params: Record<string, string | number | boolean> = {};
  Object.entries(opts.query || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') params[k] = v;
  });

  try {
    const response = await http.request({
      url: path,
      method,
      params,
      data: opts.body,
      headers: {
        ...(isMutation ? { 'X-CSRF-Token': CSRF_TOKEN } : {}),
        ...(opts.headers || {}),
      },
      timeout: opts.timeout,
    });
    const payload = response.data;
    return {
      data: unwrap<T>(payload),
      raw: payload,
      status: response.status,
      meta: payload?.meta,
    };
  } catch (e) {
    const err = e as AxiosError<any>;
    const status = err.response?.status ?? 0;
    const d = err.response?.data;
    throw new ApiError(
      errorMessage(err),
      status,
      d?.error?.code || d?.detail?.error?.code || d?.detail?.code,
      d,
    );
  }
}

export const get = <T = any>(path: string, query?: CallOptions['query']) =>
  call<T>('GET', path, { query });
export const post = <T = any>(path: string, body?: unknown, query?: CallOptions['query']) =>
  call<T>('POST', path, { body, query });
export const patch = <T = any>(path: string, body?: unknown, query?: CallOptions['query']) =>
  call<T>('PATCH', path, { body, query });

/** Replace `{name}` placeholders in a path template. */
export function fill(
  template: string,
  values: Record<string, string | number | undefined | null>,
): string {
  return template.replace(/\{([^}]+)\}/g, (_, key) =>
    values[key] === undefined || values[key] === null
      ? ''
      : encodeURIComponent(String(values[key])),
  );
}

// ---------------------------------------------------------------------------
// Domain helpers — exact live paths from the mounted OpenAPI document.
// ---------------------------------------------------------------------------

export const endpoints = {
  session: () => get('/session'),

  clients: {
    list: () => get<{ clients: any[]; count: number }>('/clients/'),
    detail: (id: string) => get(`/clients/${id}`),
    portfolio: (id: string) => get(`/clients/${id}/portfolio`),
    shariahReport: (id: string) => get(`/clients/${id}/shariah-report`),
    relationships: (id: string) => get(`/clients/${id}/relationships`),
    familyGraph: (id: string) => get(`/clients/${id}/family-graph`),
    memory: (id: string) => get(`/clients/${id}/memory`),
  },

  demoClients: {
    list: () => get<{ clients: any[]; count: number }>('/demo-clients'),
    detail: (id: string) => get(`/demo-clients/${id}`),
    currencyExposure: (id: string) => get(`/demo-clients/${id}/portfolio/currency-exposure`),
    assetBreakdown: (id: string) => get(`/demo-clients/${id}/portfolio/asset-class-breakdown`),
    futurePlanner: (id: string, body: unknown) =>
      call('POST', `/demo-clients/${id}/future-planner`, { body, timeout: 60000 }),
    investorsLikeMe: (id: string) => get(`/demo-clients/${id}/investors-like-me`),
  },

  dashboard: {
    myDay: (rmId = 'RM001') => get('/dashboard/my-day', { rm_id: rmId }),
    kpis: (rmId = 'RM001') => get('/dashboard/kpis', { rm_id: rmId }),
    bookStats: (rmId = 'RM001') => get('/dashboard/book-stats', { rm_id: rmId }),
    allocation: () => get('/dashboard/allocation'),
    performance: (period = 'ytd') => get('/dashboard/performance-trend', { period }),
  },

  market: {
    quotes: (symbols: string) => get('/market/quotes', { symbols }),
    news: (limit = 20, symbols?: string, lang?: string) =>
      get('/market/news', { limit, symbols, lang }),
    snapshot: () => get('/market/snapshot'),
    signals: (symbols: string) => get('/market/signals', { symbols }),
    historical: (symbol: string) => get(`/market/historical/${symbol}`),
    setMode: (mode: string) => post('/market/mode', undefined, { mode }),
  },

  priorities: {
    evaluations: () => get('/priorities/evaluations'),
    snooze: (clientId: string, until: string) => post(`/priorities/${clientId}/snooze`, { until }),
    dismiss: (clientId: string) => post(`/priorities/${clientId}/dismiss`, {}),
    pin: (clientId: string) => post(`/priorities/${clientId}/pin`, {}),
    evaluate: (bookId: string, body: unknown = {}) =>
      post(`/books/${bookId}/priority-evaluations`, body),
    // API-016 requires both query params; omitting them returns HTTP 422.
    latest: (bookId: string, params?: { date?: string; timezone?: string }) =>
      get(`/books/${bookId}/priority-evaluations/latest`, params),
    evaluation: (bookId: string, evaluationId: string) =>
      get(`/books/${bookId}/priority-evaluations/${evaluationId}`),
    control: (bookId: string, body: unknown) => post(`/books/${bookId}/priority-controls`, body),
    contactOutcome: (bookId: string, body: unknown) =>
      post(`/books/${bookId}/contact-outcomes`, body),
  },

  workflows: {
    list: (bookId: string, clientId?: string) =>
      get('/workflow', { book_id: bookId, client_id: clientId }),
    detail: (id: string) => get(`/workflow/${id}`),
    skills: () => get('/workflow/skills'),
    create: (body: unknown) => post('/workflow', body),
    runStage: (id: string, stageKey: string, body: unknown = {}) =>
      post(`/workflow/${id}/stages/${stageKey}/runs`, body),
    pause: (id: string, body: unknown = {}) => post(`/workflow/${id}/pause`, body),
    resume: (id: string, body: unknown = {}) => post(`/workflow/${id}/resume`, body),
    abandon: (id: string, body: unknown = {}) => post(`/workflow/${id}/abandon`, body),
    stageRun: (id: string, runId: string) => get(`/workflow/${id}/runs/${runId}`),
  },

  briefs: {
    listByClient: (clientId: string) => get('/briefs', { client_id: clientId }),
    generateLegacy: (clientId: string, force = false) =>
      post('/briefs/generate', { client_id: clientId, force_regenerate: force }),
    generate: (body: unknown) => post('/briefs/briefs', body),
    detail: (id: string) => get(`/briefs/briefs/${id}`),
    review: (id: string, body: unknown) => post(`/briefs/briefs/${id}/reviews`, body),
    edit: (id: string, body: unknown) => patch(`/briefs/briefs/${id}`, body),
    byWorkflow: (workflowId: string) => get(`/briefs/workflows/${workflowId}/briefs`),
  },

  products: {
    interpret: (workflowId: string, body: unknown) =>
      post(`/products/${workflowId}/interpretations`, body),
    editFilters: (artifactId: string, body: unknown) =>
      patch(`/products/artifacts/${artifactId}/filters`, body),
    search: (workflowId: string, body: unknown) => post(`/products/${workflowId}/searches`, body),
    compare: (workflowId: string, body: unknown) =>
      post(`/products/${workflowId}/comparisons`, body),
    select: (workflowId: string, body: unknown) =>
      post(`/products/${workflowId}/selections`, body),
    assess: (workflowId: string, body: unknown) =>
      post(`/products/${workflowId}/assessments`, body),
    override: (assessmentId: string, body: unknown) =>
      post(`/products/assessments/${assessmentId}/overrides`, body),
  },

  shariah: {
    estimate: (workflowId: string, body: unknown) =>
      post(`/workflows/${workflowId}/shariah/estimates`, body),
    evidence: (productRef: string) => get(`/workflows/shariah/evidence/${productRef}`),
  },

  family: {
    relationships: (clientId: string) => get(`/clients/${clientId}/relationships`),
    addRelationship: (clientId: string, body: unknown) =>
      post(`/clients/${clientId}/relationships`, body),
    graph: (clientId: string) => get(`/clients/${clientId}/family-graph`),
    createHousehold: (body: unknown) => post('/households', body),
    addMember: (householdId: string, body: unknown) =>
      post(`/households/${householdId}/members`, body),
    householdContext: (workflowId: string) => get(`/workflows/${workflowId}/household-context`),
  },

  memory: {
    get: (clientId: string) => get(`/clients/${clientId}/memory`),
    propose: (clientId: string, body: unknown) =>
      post(`/clients/${clientId}/memory/proposals`, body),
  },

  messages: {
    list: (workflowId: string) => get(`/workflows/${workflowId}/messages`),
    generate: (workflowId: string, body: unknown) =>
      post(`/workflows/${workflowId}/messages`, body),
    edit: (artifactId: string, body: unknown) =>
      patch(`/workflows/messages/${artifactId}`, body),
  },

  actions: {
    preview: (body: unknown) => post('/actions/preview', body),
    authorize: (previewId: string, body: unknown = {}) =>
      post(`/actions/${previewId}/authorize`, body),
    execute: (body: unknown) => post('/actions/execute', body),
    status: (actionId: string) => get(`/actions/${actionId}`),
  },

  artifacts: {
    detail: (id: string) => get(`/artifacts/artifacts/${id}`),
    edit: (id: string, body: unknown) => patch(`/artifacts/artifacts/${id}`, body),
  },

  calendar: {
    events: (body: Record<string, any> = {}) => get('/calendar/calendar/events', body),
    resolve: (eventId: string, body: unknown) =>
      post(`/calendar/calendar/events/${eventId}/resolutions`, body),
  },

  meetings: {
    detail: (id: string) => get(`/meetings/meetings/${id}`),
    consent: (id: string) => get(`/meetings/${id}/consent`),
    recordConsent: (id: string, body: unknown) => post(`/meetings/${id}/consent`, body),
    withdrawConsent: (id: string, consentId: string, body: unknown = {}) =>
      post(`/meetings/${id}/consents/${consentId}/withdraw`, body),
    startCapture: (id: string, body: unknown = {}) =>
      post(`/meetings/${id}/capture/start`, body),
    appendSegments: (id: string, body: unknown) =>
      post(`/meetings/${id}/capture/segments`, body),
    editExtraction: (extractionId: string, body: unknown) =>
      patch(`/extractions/${extractionId}/edits`, body),
  },

  admin: {
    gates: (tenantId?: string) => get('/admin/config/gates', { tenant_id: tenantId }),
    gate: (key: string) => get(`/admin/config/gates/${key}`),
    updateGate: (key: string, body: unknown, tenantId?: string) =>
      patch(`/admin/config/gates/${key}`, body, tenantId ? { tenant_id: tenantId } : undefined),
    audit: (query: Record<string, any> = {}) => get('/admin/audit', query),
    metrics: (query: Record<string, any>) => get('/admin/telemetry/metrics', query),
    recordEvent: (body: unknown) => post('/telemetry/telemetry/events', body),
  },
};
