import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import type { Envelope, ErrorResponse } from './contracts/common';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Typed API client with canonical envelope handling
class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL: `${baseURL}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // Include session cookies
    });

    // Response interceptor for envelope unwrapping and error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ErrorResponse>) => {
        if (error.response?.data?.error) {
          // Canonical error response
          const apiError = error.response.data.error;
          const enrichedError = new Error(apiError.message);
          Object.assign(enrichedError, {
            code: apiError.code,
            fields: apiError.fields,
            retryable: apiError.retryable,
            status_url: apiError.status_url,
            status: error.response.status,
            request_id: error.response.data.meta.request_id,
          });
          return Promise.reject(enrichedError);
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<Envelope<T>> {
    const response = await this.client.get<Envelope<T>>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<Envelope<T>> {
    const response = await this.client.post<Envelope<T>>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<Envelope<T>> {
    const response = await this.client.put<Envelope<T>>(url, data, config);
    return response.data;
  }

  async patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<Envelope<T>> {
    const response = await this.client.patch<Envelope<T>>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<Envelope<T>> {
    const response = await this.client.delete<Envelope<T>>(url, config);
    return response.data;
  }
}

export const apiClient = new ApiClient(API_BASE_URL);

// Dashboard API - used by app/dashboard/page.tsx
export const dashboardApi = {
  getMyDay: (rmId: string = 'RM001') =>
    axios.get(`${API_BASE_URL}/api/v1/dashboard/my-day?rm_id=${rmId}`),
  getKPIs: (rmId: string = 'RM001') =>
    axios.get(`${API_BASE_URL}/api/v1/dashboard/kpis?rm_id=${rmId}`),
  getBookStats: (rmId: string = 'RM001') =>
    axios.get(`${API_BASE_URL}/api/v1/dashboard/book-stats?rm_id=${rmId}`),
  getAllocation: (rmId: string = 'RM001') =>
    axios.get(`${API_BASE_URL}/api/v1/dashboard/allocation?rm_id=${rmId}`),
  getPerformanceTrend: (rmId: string = 'RM001', period: string = 'ytd') =>
    axios.get(`${API_BASE_URL}/api/v1/dashboard/performance-trend?rm_id=${rmId}&period=${period}`),
};

// Market API - used by app/dashboard/page.tsx
export const marketApi = {
  getNews: (symbols?: string[], limit: number = 20) =>
    axios.get(`${API_BASE_URL}/api/v1/market/news${symbols ? `?symbols=${symbols.join(',')}&limit=${limit}` : `?limit=${limit}`}`),
};

// Brief API - used by components/BriefModal.tsx
export const briefApi = {
  generate: (clientId: string, forceRegenerate: boolean = false) =>
    axios.post(`${API_BASE_URL}/api/v1/briefs/generate`, { client_id: clientId, force_regenerate: forceRegenerate }),
  approve: (briefId: string, approvedBy: string, editedAgenda?: string) =>
    axios.post(`${API_BASE_URL}/api/v1/briefs/approve`, { brief_id: briefId, approved_by: approvedBy, edited_agenda: editedAgenda }),
  getBrief: (briefId: string) =>
    axios.get(`${API_BASE_URL}/api/v1/briefs/${briefId}`),
};
