/**
 * Compatibility layer for the screens that predate the canonical API client.
 *
 * New code should import from `@/lib/endpoints` directly. This module keeps the
 * old call signatures working while routing them through the same live API
 * client (with CSRF headers and envelope unwrapping).
 */
import { call, get, post, patch, endpoints, API_BASE, CSRF_TOKEN, Method } from './endpoints';
import type { Envelope } from './contracts/common';

const API_BASE_URL = API_BASE;
export { API_BASE_URL, CSRF_TOKEN };

/** Repair paths that were written against routes that do not exist. */
export function normalizeLegacyPath(path: string): string {
  let p = path;
  if (p === '/clients') return '/clients/';
  if (p.startsWith('/workflows?')) return '/workflow?' + p.slice('/workflows?'.length);
  if (/^\/workflow\/[^/]+\/messages$/.test(p)) return p.replace('/workflow/', '/workflows/');
  return p;
}

export const apiClient = {
  get: async <T>(url: string): Promise<Envelope<T>> => {
    const [path, qs] = normalizeLegacyPath(url).split('?');
    const query = Object.fromEntries(new URLSearchParams(qs || ''));
    const res = await get<T>(path, query);
    return { data: res.data, meta: res.meta as any };
  },
  post: async <T>(url: string, data?: unknown): Promise<Envelope<T>> => {
    const res = await post<T>(normalizeLegacyPath(url), data);
    return { data: res.data, meta: res.meta as any };
  },
  patch: async <T>(url: string, data?: unknown): Promise<Envelope<T>> => {
    const res = await patch<T>(normalizeLegacyPath(url), data);
    return { data: res.data, meta: res.meta as any };
  },
  put: async <T>(url: string, data?: unknown): Promise<Envelope<T>> => {
    const res = await call<T>('PUT', normalizeLegacyPath(url), { body: data });
    return { data: res.data, meta: res.meta as any };
  },
  delete: async <T>(url: string): Promise<Envelope<T>> => {
    const res = await call<T>('DELETE', normalizeLegacyPath(url));
    return { data: res.data, meta: res.meta as any };
  },
};

// Axios-shaped adapters used by the older dashboard and modal components.
const asResponse = (res: { data: unknown; raw: unknown }) => ({ data: res.data as any });

export const dashboardApi = {
  getMyDay: async (rmId = 'RM001') => asResponse(await endpoints.dashboard.myDay(rmId)),
  getKPIs: async (rmId = 'RM001') => asResponse(await endpoints.dashboard.kpis(rmId)),
  getBookStats: async (rmId = 'RM001') => asResponse(await endpoints.dashboard.bookStats(rmId)),
  getAllocation: async (rmId = 'RM001') => asResponse(await endpoints.dashboard.allocation()),
  getPerformanceTrend: async (rmId = 'RM001', period = 'ytd') =>
    asResponse(await endpoints.dashboard.performance(period)),
};

export const marketApi = {
  getNews: async (symbols?: string[], limit = 20) =>
    asResponse(await endpoints.market.news(limit, symbols?.join(','))),
};

export const briefApi = {
  generate: async (clientId: string, forceRegenerate = false) =>
    asResponse(await endpoints.briefs.generateLegacy(clientId, forceRegenerate)),
  // Canonical review lives on /briefs/briefs/{id}/reviews and requires an
  // artifact revision + If-Match. The legacy modal no longer pretends to
  // approve; it links to the briefs workspace instead.
  approve: async (briefId: string, _approvedBy: string, _editedAgenda?: string) => {
    throw new Error('Use the Client Briefs workspace to record a section review.');
  },
  getBrief: async (briefId: string) => asResponse(await endpoints.briefs.detail(briefId)),
};

// Portfolio pages expect the raw (still enveloped) response.
const rawResponse = (res: { raw: unknown }) => ({ data: res.raw as any });

export const demoClientApi = {
  list: async () => rawResponse(await call('GET', '/demo-clients')),
  get: async (id: string) => rawResponse(await endpoints.demoClients.detail(id)),
  currencyExposure: async (id: string) => rawResponse(await endpoints.demoClients.currencyExposure(id)),
  assetBreakdown: async (id: string) => rawResponse(await endpoints.demoClients.assetBreakdown(id)),
  futurePlanner: async (id: string, params: Record<string, unknown>) =>
    rawResponse(await endpoints.demoClients.futurePlanner(id, params)),
  investorsLikeMe: async (id: string) => rawResponse(await endpoints.demoClients.investorsLikeMe(id)),
};
